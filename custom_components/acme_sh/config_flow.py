"""Config flow for ACME.sh integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

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
    DEFAULT_DNS_PROVIDER,
    DEFAULT_AUTO_RENEW,
    DEFAULT_RENEW_INTERVAL,
    ACME_SERVERS,
    KEYLENGTH_OPTIONS,
    DNS_PROVIDERS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("domains"): str,
        vol.Required(CONF_DNS_PROVIDER, default=DEFAULT_DNS_PROVIDER): vol.In(DNS_PROVIDERS),
        vol.Required(CONF_DNS_ENV): str,
        vol.Optional(CONF_KEYLENGTH, default=DEFAULT_KEYLENGTH): vol.In(KEYLENGTH_OPTIONS),
        vol.Optional(CONF_DAYS, default=DEFAULT_DAYS): vol.All(vol.Coerce(int), vol.Range(min=1, max=180)),
        vol.Optional(CONF_STAGING, default=False): bool,
        vol.Optional(CONF_ACME_SERVER, default=DEFAULT_ACME_SERVER): vol.In(ACME_SERVERS),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    domains = [d.strip() for d in data["domains"].split(",")]
    
    return {
        "title": f"ACME.sh - {domains[0]}",
        "email": data["email"],
        "domains": domains,
        CONF_DNS_PROVIDER: data[CONF_DNS_PROVIDER],
        CONF_DNS_ENV: data[CONF_DNS_ENV],
        CONF_KEYLENGTH: data[CONF_KEYLENGTH],
        CONF_DAYS: data[CONF_DAYS],
        CONF_STAGING: data[CONF_STAGING],
        CONF_ACME_SERVER: data[CONF_ACME_SERVER],
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ACME.sh."""
    
    VERSION = 1
    
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=info)
        
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the integration."""
    
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
    
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        options = self.config_entry.options
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_AUTO_RENEW,
                        default=options.get(CONF_AUTO_RENEW, DEFAULT_AUTO_RENEW),
                    ): bool,
                    vol.Optional(
                        CONF_RENEW_INTERVAL,
                        default=options.get(CONF_RENEW_INTERVAL, DEFAULT_RENEW_INTERVAL),
                    ): str,
                }
            ),
        )
