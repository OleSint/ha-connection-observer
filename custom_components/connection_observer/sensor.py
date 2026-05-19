"""Sensor entities for Connection Observer."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    async_add_entities(
        [
            OfflineCountSensor(coordinator),
            PendingEventsSensor(coordinator),
        ]
    )


class _CoordinatorEntity(SensorEntity):
    """Base class wiring up the coordinator listener."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, coordinator: ConnectionObserverCoordinator) -> None:
        self._coordinator = coordinator

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class OfflineCountSensor(_CoordinatorEntity):
    """Number of devices currently offline (open, unresolved events)."""

    _attr_icon = "mdi:lan-disconnect"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "devices"

    def __init__(self, coordinator: ConnectionObserverCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_offline_count"
        self._attr_name = "Offline Devices"

    @property
    def native_value(self) -> int:
        return sum(
            1 for ev in self._coordinator.events if ev.reconnected_at is None
        )

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "devices": [
                ev.device_name
                for ev in self._coordinator.events
                if ev.reconnected_at is None
            ]
        }


class PendingEventsSensor(_CoordinatorEntity):
    """Number of disconnect events not yet included in a summary."""

    _attr_icon = "mdi:clock-alert-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "events"

    def __init__(self, coordinator: ConnectionObserverCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_pending_events"
        self._attr_name = "Pending Summary Events"

    @property
    def native_value(self) -> int:
        return sum(
            1 for ev in self._coordinator.events if not ev.included_in_summary
        )
