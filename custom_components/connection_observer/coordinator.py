"""Core coordinator for Connection Observer."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.event import async_call_later, async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_EXCLUDED_ENTITIES,
    CONF_LANGUAGE,
    CONF_NOTIFY_IMMEDIATE,
    CONF_NOTIFY_RECONNECT,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_SUMMARY,
    CONF_PROTOCOLS,
    CONF_SUMMARY_DAYS,
    CONF_SUMMARY_TIME,
    LANG_DE,
    STORAGE_KEY,
    STORAGE_VERSION,
    STARTUP_GRACE_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

# How many days to keep events in storage before pruning
EVENT_RETENTION_DAYS = 30


@dataclass
class DisconnectEvent:
    """A single device disconnect/reconnect event."""

    device_key: str          # device_id or entity_id if no device
    device_name: str
    protocol: str
    disconnected_at: datetime
    reconnected_at: datetime | None = None
    included_in_summary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_key": self.device_key,
            "device_name": self.device_name,
            "protocol": self.protocol,
            "disconnected_at": self.disconnected_at.isoformat(),
            "reconnected_at": self.reconnected_at.isoformat() if self.reconnected_at else None,
            "included_in_summary": self.included_in_summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DisconnectEvent":
        event = cls(
            device_key=data["device_key"],
            device_name=data["device_name"],
            protocol=data["protocol"],
            disconnected_at=datetime.fromisoformat(data["disconnected_at"]),
        )
        if data.get("reconnected_at"):
            event.reconnected_at = datetime.fromisoformat(data["reconnected_at"])
        event.included_in_summary = data.get("included_in_summary", False)
        return event


def _parse_summary_time(time_str: str) -> tuple[int, int]:
    """Parse 'HH:MM' or 'HH:MM:SS' to (hour, minute)."""
    try:
        parts = str(time_str).split(":")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 8, 0


class ConnectionObserverCoordinator:
    """Manages event listeners, state tracking, and notifications."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
        self._events: list[DisconnectEvent] = []
        self._last_summary: datetime | None = None
        self._unsub: list = []
        self._startup_complete = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_setup(self) -> None:
        await self._load_store()
        self._setup_startup_guard()
        self._setup_state_listener()
        self._setup_summary_scheduler()

    async def async_unload(self) -> None:
        for unsub in self._unsub:
            unsub()
        self._unsub.clear()
        await self._save_store()

    async def async_update_options(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Reconfigure listeners after options change."""
        for unsub in self._unsub:
            unsub()
        self._unsub.clear()
        self._startup_complete = True  # already running, no grace period needed
        self._setup_state_listener()
        self._setup_summary_scheduler()

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _setup_startup_guard(self) -> None:
        """Delay event tracking until HA is fully started."""
        if self.hass.state == CoreState.running:
            self._startup_complete = True
            return

        @callback
        def _on_ha_started(_event: Event) -> None:
            # Still give entities a moment to restore their states
            async_call_later(self.hass, STARTUP_GRACE_SECONDS, self._mark_startup_complete)

        self._unsub.append(
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_ha_started)
        )

    @callback
    def _mark_startup_complete(self, _now: Any) -> None:
        self._startup_complete = True
        _LOGGER.debug("Connection Observer startup grace period ended, tracking active")

    def _setup_state_listener(self) -> None:
        self._unsub.append(
            self.hass.bus.async_listen("state_changed", self._handle_state_change)
        )

    def _setup_summary_scheduler(self) -> None:
        cfg = self._cfg
        if not cfg.get(CONF_NOTIFY_SUMMARY):
            return

        hour, minute = _parse_summary_time(cfg.get(CONF_SUMMARY_TIME, "08:00"))
        days: list[str] = cfg.get(CONF_SUMMARY_DAYS, [str(i) for i in range(7)])
        day_ints = {int(d) for d in days}

        @callback
        def _on_time(now: datetime) -> None:
            if now.weekday() in day_ints:
                self.hass.async_create_task(self._send_summary())

        self._unsub.append(
            async_track_time_change(self.hass, _on_time, hour=hour, minute=minute, second=0)
        )

    # ------------------------------------------------------------------
    # State change handling
    # ------------------------------------------------------------------

    @callback
    def _handle_state_change(self, event: Event) -> None:
        if not self._startup_complete:
            return

        entity_id: str | None = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if not entity_id or not new_state or not old_state:
            return

        excluded: list[str] = self._cfg.get(CONF_EXCLUDED_ENTITIES, [])
        if entity_id in excluded:
            return

        protocol = self._get_entity_protocol(entity_id)
        if not protocol:
            return

        monitored: list[str] = self._cfg.get(CONF_PROTOCOLS, [])
        if protocol not in monitored:
            return

        going_unavailable = new_state.state == "unavailable" and old_state.state != "unavailable"
        coming_back = old_state.state == "unavailable" and new_state.state != "unavailable"

        if going_unavailable:
            self._on_disconnect(entity_id, protocol)
        elif coming_back:
            self._on_reconnect(entity_id)

    @callback
    def _on_disconnect(self, entity_id: str, protocol: str) -> None:
        device_key, device_name = self._resolve_device(entity_id)

        # Deduplicate: if there's already an open event for this device, skip
        for ev in self._events:
            if ev.device_key == device_key and ev.reconnected_at is None:
                return

        evt = DisconnectEvent(
            device_key=device_key,
            device_name=device_name,
            protocol=protocol,
            disconnected_at=dt_util.now(),
        )
        self._events.append(evt)
        _LOGGER.info("Connection Observer: %s (%s) went offline", device_name, protocol)

        self.hass.async_create_task(self._save_store())

        if self._cfg.get(CONF_NOTIFY_IMMEDIATE):
            self.hass.async_create_task(self._send_immediate(evt))

    @callback
    def _on_reconnect(self, entity_id: str) -> None:
        device_key, _ = self._resolve_device(entity_id)
        now = dt_util.now()
        changed = False

        for ev in self._events:
            if ev.device_key == device_key and ev.reconnected_at is None:
                ev.reconnected_at = now
                changed = True
                _LOGGER.info("Connection Observer: %s came back online", ev.device_name)
                break

        if changed:
            self.hass.async_create_task(self._save_store())
            if self._cfg.get(CONF_NOTIFY_RECONNECT):
                device_name = next(
                    (ev.device_name for ev in self._events if ev.device_key == device_key),
                    entity_id,
                )
                self.hass.async_create_task(self._send_reconnect(device_name))

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def _notify_services(self) -> list[str]:
        """Return configured notify services as a list (supports legacy single string)."""
        raw = self._cfg.get(CONF_NOTIFY_SERVICE, [])
        if isinstance(raw, str):
            return [raw] if raw else []
        return [s for s in raw if s]

    async def _send_immediate(self, evt: DisconnectEvent) -> None:
        services = self._notify_services()
        if not services:
            return

        lang = self._cfg.get(CONF_LANGUAGE, "en")
        time_str = evt.disconnected_at.strftime("%H:%M")

        if lang == LANG_DE:
            title = "Verbindungsabbruch"
            msg = f"⚠️ {evt.device_name} ({evt.protocol}) hat um {time_str} die Verbindung verloren."
        else:
            title = "Connection Lost"
            msg = f"⚠️ {evt.device_name} ({evt.protocol}) lost connection at {time_str}."

        await self._notify_all(services, title, msg)

    async def _send_reconnect(self, device_name: str) -> None:
        services = self._notify_services()
        if not services:
            return

        lang = self._cfg.get(CONF_LANGUAGE, "en")
        if lang == LANG_DE:
            title = "Verbindung wiederhergestellt"
            msg = f"✅ {device_name} ist wieder online."
        else:
            title = "Connection Restored"
            msg = f"✅ {device_name} is back online."

        await self._notify_all(services, title, msg)

    async def _send_summary(self) -> None:
        services = self._notify_services()
        if not services:
            return

        pending = [ev for ev in self._events if not ev.included_in_summary]
        if not pending:
            return

        lang = self._cfg.get(CONF_LANGUAGE, "en")

        if lang == LANG_DE:
            title = "Verbindungs-Zusammenfassung"
            lines = [f"📋 {len(pending)} Gerät(e) seit der letzten Zusammenfassung betroffen:"]
            for ev in pending:
                d_time = ev.disconnected_at.strftime("%d.%m. %H:%M")
                if ev.reconnected_at:
                    r_time = ev.reconnected_at.strftime("%H:%M")
                    lines.append(
                        f"• {ev.device_name} ({ev.protocol}): offline seit {d_time}, "
                        f"wieder online um {r_time}"
                    )
                else:
                    lines.append(
                        f"• {ev.device_name} ({ev.protocol}): offline seit {d_time} ⚠️ noch offline"
                    )
        else:
            title = "Connection Summary"
            lines = [f"📋 {len(pending)} device(s) affected since last summary:"]
            for ev in pending:
                d_time = ev.disconnected_at.strftime("%m/%d %H:%M")
                if ev.reconnected_at:
                    r_time = ev.reconnected_at.strftime("%H:%M")
                    lines.append(
                        f"• {ev.device_name} ({ev.protocol}): offline since {d_time}, "
                        f"back online at {r_time}"
                    )
                else:
                    lines.append(
                        f"• {ev.device_name} ({ev.protocol}): offline since {d_time} ⚠️ still offline"
                    )

        await self._notify_all(services, title, "\n".join(lines))

        for ev in pending:
            ev.included_in_summary = True
        self._last_summary = dt_util.now()
        await self._save_store()

    async def _notify_all(self, services: list[str], title: str, message: str) -> None:
        """Send notification to every configured service."""
        for service in services:
            await self._notify_one(service, title, message)

    async def _notify_one(self, service: str, title: str, message: str) -> None:
        parts = service.split(".", 1)
        if len(parts) != 2:
            _LOGGER.error("Invalid notify service format: %s", service)
            return
        domain, service_name = parts
        try:
            await self.hass.services.async_call(
                domain, service_name, {"title": title, "message": message}, blocking=False
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Failed to send notification via %s: %s", service, err)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _cfg(self) -> dict[str, Any]:
        return {**self.entry.data, **self.entry.options}

    def _get_entity_protocol(self, entity_id: str) -> str | None:
        er = async_get_entity_registry(self.hass)
        entry = er.async_get(entity_id)
        return entry.platform if entry else None

    def _resolve_device(self, entity_id: str) -> tuple[str, str]:
        """Return (device_key, display_name) for an entity."""
        er = async_get_entity_registry(self.hass)
        dr = async_get_device_registry(self.hass)

        entity_entry = er.async_get(entity_id)
        if entity_entry and entity_entry.device_id:
            device = dr.async_get(entity_entry.device_id)
            if device:
                name = device.name_by_user or device.name or entity_id
                return device.id, name

        state = self.hass.states.get(entity_id)
        name = state.attributes.get("friendly_name", entity_id) if state else entity_id
        return entity_id, name

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    async def _load_store(self) -> None:
        data = await self._store.async_load()
        if not data:
            return
        self._events = [DisconnectEvent.from_dict(e) for e in data.get("events", [])]
        if last := data.get("last_summary"):
            self._last_summary = datetime.fromisoformat(last)

    async def _save_store(self) -> None:
        cutoff = dt_util.now() - timedelta(days=EVENT_RETENTION_DAYS)
        self._events = [ev for ev in self._events if ev.disconnected_at > cutoff]
        await self._store.async_save(
            {
                "events": [ev.to_dict() for ev in self._events],
                "last_summary": self._last_summary.isoformat() if self._last_summary else None,
            }
        )
