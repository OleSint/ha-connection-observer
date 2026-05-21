"""Binary sensor entities for Connection Observer."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ConnectionObserverCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ConnectionObserverCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ConnectionStatusSensor(coordinator)])


class ConnectionStatusSensor(BinarySensorEntity):
    """
    'Problem' binary sensor — ON means at least one device is currently offline.
    Use this as a condition in automations or as a dashboard status indicator.
    """

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:check-network"

    def __init__(self, coordinator: ConnectionObserverCoordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.entry.entry_id}_all_ok"
        self._attr_name = "Connection Problem"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return True (= problem detected) when any device is still offline."""
        return any(
            ev.reconnected_at is None for ev in self._coordinator.events
        )
