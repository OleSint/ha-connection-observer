"""Connection Observer – monitors device connectivity and sends notifications."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .coordinator import ConnectionObserverCoordinator

_LOGGER = logging.getLogger(__name__)

_PLATFORMS = ["sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = ConnectionObserverCoordinator(hass, entry)
    await coordinator.async_setup()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(coordinator.async_update_options))

    # Register services once (guard against multiple config entries)
    if not hass.services.has_service(DOMAIN, "send_summary_now"):

        async def _send_summary_now(call: ServiceCall) -> None:  # noqa: ARG001
            for coord in hass.data[DOMAIN].values():
                await coord.async_send_summary_now()

        async def _clear_history(call: ServiceCall) -> None:  # noqa: ARG001
            for coord in hass.data[DOMAIN].values():
                await coord.async_clear_history()

        hass.services.async_register(DOMAIN, "send_summary_now", _send_summary_now)
        hass.services.async_register(DOMAIN, "clear_history", _clear_history)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)

    coordinator: ConnectionObserverCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.async_unload()

    # Remove services when the last entry is gone
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "send_summary_now")
        hass.services.async_remove(DOMAIN, "clear_history")

    return unload_ok
