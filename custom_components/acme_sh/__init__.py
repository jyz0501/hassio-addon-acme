"""ACME.sh SSL Certificate Manager integration for Home Assistant."""
import asyncio
import logging
import os
import subprocess
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

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

PLATFORMS: list[str] = []


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
            else:
                _LOGGER.error("Certificate renewal failed: %s", stderr.decode())
        except Exception as e:
            _LOGGER.error("Error renewing certificate: %s", e)
    
    hass.services.async_register(DOMAIN, "issue_certificate", async_issue_certificate)
    hass.services.async_register(DOMAIN, "renew_certificate", async_renew_certificate)
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ACME.sh from a config entry."""
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
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
