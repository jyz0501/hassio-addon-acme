"""ACME.sh SSL Certificate Manager integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.components.sensor import SensorEntity

from .const import (
    DOMAIN,
    CONF_DNS_PROVIDER,
    CONF_DNS_ENV,
    CONF_KEYLENGTH,
    CONF_DAYS,
    CONF_STAGING,
    CONF_ACME_SERVER,
    CONF_AUTO_RENEW,
    CONF_RENEW_INTERVAL,
    DEFAULT_KEYLENGTH,
    DEFAULT_DAYS,
    DEFAULT_ACME_SERVER,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the ACME.sh component."""
    hass.data.setdefault(DOMAIN, {})
    
    async def async_issue_certificate(call):
        """Issue or renew SSL certificate."""
        email = call.data.get("email")
        domains = call.data.get("domains", [])
        dns_provider = call.data.get("dns_provider", "dns_cf")
        dns_env = call.data.get("dns_env", {})
        keylength = call.data.get("keylength", DEFAULT_KEYLENGTH)
        staging = call.data.get("staging", False)
        acme_server = call.data.get("acme_server", DEFAULT_ACME_SERVER)
        force = call.data.get("force", False)
        
        if not email or not domains:
            _LOGGER.error("Email and domains are required")
            return
        
        acme_sh_path = Path(hass.config.path("acme.sh"))
        
        cmd = [
            str(acme_sh_path / "acme.sh"),
            "--issue",
            "--dns", dns_provider,
        ]
        
        for domain in domains:
            cmd.extend(["-d", domain])
        
        cmd.extend(["--keylength", keylength])
        cmd.extend(["--config-home", str(acme_sh_path)])
        
        if staging:
            cmd.append("--staging")
        
        if force:
            cmd.append("--force")
        
        env = os.environ.copy()
        env.update(dns_env)
        
        _LOGGER.info("Issuing certificate for domains: %s", domains)
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                _LOGGER.info("Certificate issued successfully")
                
                main_domain = domains[0]
                ssl_dir = Path(hass.config.path("ssl"))
                ssl_dir.mkdir(exist_ok=True)
                
                install_cmd = [
                    str(acme_sh_path / "acme.sh"),
                    "--install-cert",
                    "-d", main_domain,
                    "--config-home", str(acme_sh_path),
                    "--cert-file", str(ssl_dir / f"{main_domain}.pem"),
                    "--key-file", str(ssl_dir / f"{main_domain}-key.pem"),
                    "--fullchain-file", str(ssl_dir / f"{main_domain}-fullchain.pem"),
                ]
                
                install_proc = await asyncio.create_subprocess_exec(
                    *install_cmd,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await install_proc.communicate()
                
                hass.bus.async_fire(f"{DOMAIN}_certificate_issued", {
                    "domains": domains,
                    "main_domain": main_domain,
                })
                
                for entry_id in hass.data[DOMAIN]:
                    if isinstance(hass.data[DOMAIN][entry_id], dict):
                        coordinator = hass.data[DOMAIN][entry_id].get("coordinator")
                        if coordinator:
                            await coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to issue certificate: %s", stderr.decode())
                hass.bus.async_fire(f"{DOMAIN}_certificate_failed", {
                    "domains": domains,
                    "error": stderr.decode(),
                })
        except Exception as e:
            _LOGGER.error("Error issuing certificate: %s", e)
    
    async def async_renew_certificate(call):
        """Renew SSL certificates."""
        acme_sh_path = Path(hass.config.path("acme.sh"))
        
        cmd = [
            str(acme_sh_path / "acme.sh"),
            "--cron",
            "--config-home", str(acme_sh_path),
        ]
        
        _LOGGER.info("Running certificate renewal check")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                _LOGGER.info("Certificate renewal check completed")
                hass.bus.async_fire(f"{DOMAIN}_renewal_completed")
                
                for entry_id in hass.data[DOMAIN]:
                    if isinstance(hass.data[DOMAIN][entry_id], dict):
                        coordinator = hass.data[DOMAIN][entry_id].get("coordinator")
                        if coordinator:
                            await coordinator.async_request_refresh()
            else:
                _LOGGER.error("Certificate renewal failed: %s", stderr.decode())
        except Exception as e:
            _LOGGER.error("Error renewing certificate: %s", e)
    
    hass.services.async_register(DOMAIN, "issue_certificate", async_issue_certificate)
    hass.services.async_register(DOMAIN, "renew_certificate", async_renew_certificate)
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ACME.sh from a config entry."""
    
    async def async_update_data():
        """Fetch data from acme.sh."""
        acme_sh_path = Path(hass.config.path("acme.sh"))
        domains = entry.data.get("domains", [])
        
        if not domains:
            return {}
        
        main_domain = domains[0] if isinstance(domains, list) else domains
        cert_data = {
            "domain": main_domain,
            "domains": domains,
            "status": "unknown",
            "expiry_date": None,
            "days_remaining": None,
            "issuer": None,
            "auto_renew": entry.options.get(CONF_AUTO_RENEW, True),
        }
        
        try:
            cmd = [
                str(acme_sh_path / "acme.sh"),
                "--list",
                "--config-home", str(acme_sh_path),
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if main_domain in stdout.decode():
                cert_data["status"] = "valid"
            
            ssl_dir = Path(hass.config.path("ssl"))
            cert_file = ssl_dir / f"{main_domain}-fullchain.pem"
            
            if cert_file.exists():
                openssl_cmd = [
                    "openssl",
                    "x509",
                    "-in", str(cert_file),
                    "-noout",
                    "-dates",
                    "-issuer",
                ]
                
                proc = await asyncio.create_subprocess_exec(
                    *openssl_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                
                output = stdout.decode()
                
                for line in output.split("\n"):
                    if line.startswith("notAfter="):
                        date_str = line.replace("notAfter=", "").strip()
                        try:
                            expiry_date = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
                            cert_data["expiry_date"] = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
                            cert_data["days_remaining"] = (expiry_date - datetime.now()).days
                        except ValueError:
                            pass
                    elif line.startswith("issuer="):
                        cert_data["issuer"] = line.replace("issuer=", "").strip()
                
                if cert_data["days_remaining"] is not None:
                    if cert_data["days_remaining"] < 0:
                        cert_data["status"] = "expired"
                    elif cert_data["days_remaining"] < entry.data.get(CONF_DAYS, DEFAULT_DAYS):
                        cert_data["status"] = "renewal_required"
                    else:
                        cert_data["status"] = "valid"
        
        except Exception as e:
            _LOGGER.error("Error updating certificate data: %s", e)
            raise UpdateFailed(f"Error updating certificate data: {e}")
        
        return cert_data
    
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=timedelta(hours=6),
    )
    
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config": entry.data,
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options for the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
