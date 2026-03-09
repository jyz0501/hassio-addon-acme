"""Sensor platform for ACME.sh integration."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="certificate",
        name="SSL Certificate",
        icon="mdi:certificate",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    
    async_add_entities(
        CertificateSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class CertificateSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Certificate sensor."""
    
    _attr_has_entity_name = True
    
    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        
    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("status")
        return None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
        
        data = self.coordinator.data
        attrs = {
            "domain": data.get("domain"),
            "domains": data.get("domains"),
            "expiry_date": data.get("expiry_date"),
            "days_remaining": data.get("days_remaining"),
            "issuer": data.get("issuer"),
            "auto_renew": data.get("auto_renew"),
        }
        
        return {k: v for k, v in attrs.items() if v is not None}
    
    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        status = self.coordinator.data.get("status") if self.coordinator.data else None
        
        if status == "valid":
            return "mdi:check-circle"
        elif status == "expired":
            return "mdi:alert-circle"
        elif status == "renewal_required":
            return "mdi:alert"
        else:
            return "mdi:help-circle"
