"""Core coordinator for Connection Observer."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

from homeassistant.components.repairs import IssueSeverity, async_create_issue, async_delete_issue
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, Event, HomeAssistant, callback
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.event import (
    async_call_later,
    async_track_point_in_time,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ALERT_DELAY,
    CONF_COOLDOWN,
    CONF_EXCLUDED_ENTITIES,
    CONF_INCLUDE_AREA,
    CONF_INCLUDE_DEVICE_INFO,
    CONF_LANGUAGE,
    CONF_MIN_OFFLINE_DURATION,
    CONF_NOTIFY_IMMEDIATE,
    CONF_NOTIFY_RECONNECT,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_SUMMARY,
    CONF_PROTOCOLS,
    CONF_REPAIRS_THRESHOLD,
    CONF_SUMMARY_DAYS,
    CONF_SUMMARY_TIME,
    CONF_TMPL_IMM_MSG,
    CONF_TMPL_IMM_TITLE,
    CONF_TMPL_REC_MSG,
    CONF_TMPL_REC_TITLE,
    CONF_TMPL_SUM_LINE_ONGOING,
    CONF_TMPL_SUM_LINE_RESOLVED,
    CONF_TMPL_SUM_TITLE,
    DOMAIN,
    STARTUP_GRACE_SECONDS,
    STORAGE_KEY,
    STORAGE_VERSION,
    WATCHDOG_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

EVENT_RETENTION_DAYS = 30

# ---------------------------------------------------------------------------
# Built-in message strings per language
# Variables available per key:
#   imm_title/msg : {device_name} {protocol} {time} {area} {model}
#   rec_title/msg : {device_name} {time}
#   sum_title     : {count}
#   sum_resolved  : {device_name} {area} {protocol} {time_offline} {time_online}
#   sum_ongoing   : {device_name} {area} {protocol} {time_offline}
# {area} is pre-formatted as " [Room]" or "" — include it directly after {device_name}
# ---------------------------------------------------------------------------
_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "imm_title": "Connection Lost",
        "imm_msg": "⚠️ {device_name} ({protocol}) lost connection at {time}.",
        "rec_title": "Connection Restored",
        "rec_msg": "✅ {device_name} is back online.",
        "sum_title": "Connection Summary",
        "sum_header": "📋 {count} device(s) affected since last summary:",
        "sum_resolved": "• {device_name}{area} ({protocol}): offline since {time_offline}, back online at {time_online}",
        "sum_ongoing": "• {device_name}{area} ({protocol}): offline since {time_offline} ⚠️ still offline",
    },
    "de": {
        "imm_title": "Verbindungsabbruch",
        "imm_msg": "⚠️ {device_name} ({protocol}) hat um {time} die Verbindung verloren.",
        "rec_title": "Verbindung wiederhergestellt",
        "rec_msg": "✅ {device_name} ist wieder online.",
        "sum_title": "Verbindungs-Zusammenfassung",
        "sum_header": "📋 {count} Gerät(e) seit der letzten Zusammenfassung betroffen:",
        "sum_resolved": "• {device_name}{area} ({protocol}): offline seit {time_offline}, wieder online um {time_online}",
        "sum_ongoing": "• {device_name}{area} ({protocol}): offline seit {time_offline} ⚠️ noch offline",
    },
    "fr": {
        "imm_title": "Connexion perdue",
        "imm_msg": "⚠️ {device_name} ({protocol}) a perdu la connexion à {time}.",
        "rec_title": "Connexion rétablie",
        "rec_msg": "✅ {device_name} est de nouveau en ligne.",
        "sum_title": "Résumé des connexions",
        "sum_header": "📋 {count} appareil(s) affecté(s) depuis le dernier résumé :",
        "sum_resolved": "• {device_name}{area} ({protocol}) : hors ligne depuis {time_offline}, de nouveau en ligne à {time_online}",
        "sum_ongoing": "• {device_name}{area} ({protocol}) : hors ligne depuis {time_offline} ⚠️ toujours hors ligne",
    },
    "nl": {
        "imm_title": "Verbinding verbroken",
        "imm_msg": "⚠️ {device_name} ({protocol}) heeft om {time} de verbinding verbroken.",
        "rec_title": "Verbinding hersteld",
        "rec_msg": "✅ {device_name} is weer online.",
        "sum_title": "Verbindingsoverzicht",
        "sum_header": "📋 {count} apparaat/apparaten getroffen sinds het laatste overzicht:",
        "sum_resolved": "• {device_name}{area} ({protocol}): offline sinds {time_offline}, weer online om {time_online}",
        "sum_ongoing": "• {device_name}{area} ({protocol}): offline sinds {time_offline} ⚠️ nog steeds offline",
    },
    "es": {
        "imm_title": "Conexión perdida",
        "imm_msg": "⚠️ {device_name} ({protocol}) perdió la conexión a las {time}.",
        "rec_title": "Conexión restaurada",
        "rec_msg": "✅ {device_name} está de nuevo en línea.",
        "sum_title": "Resumen de conexiones",
        "sum_header": "📋 {count} dispositivo(s) afectado(s) desde el último resumen:",
        "sum_resolved": "• {device_name}{area} ({protocol}): sin conexión desde {time_offline}, de nuevo en línea a las {time_online}",
        "sum_ongoing": "• {device_name}{area} ({protocol}): sin conexión desde {time_offline} ⚠️ todavía sin conexión",
    },
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class DisconnectEvent:
    device_key: str
    device_name: str
    protocol: str
    disconnected_at: datetime
    trigger_entity_id: str = ""
    area_name: str | None = None
    device_model: str | None = None
    reconnected_at: datetime | None = None
    included_in_summary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_key": self.device_key,
            "device_name": self.device_name,
            "protocol": self.protocol,
            "disconnected_at": self.disconnected_at.isoformat(),
            "trigger_entity_id": self.trigger_entity_id,
            "area_name": self.area_name,
            "device_model": self.device_model,
            "reconnected_at": self.reconnected_at.isoformat() if self.reconnected_at else None,
            "included_in_summary": self.included_in_summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DisconnectEvent":
        evt = cls(
            device_key=data["device_key"],
            device_name=data["device_name"],
            protocol=data["protocol"],
            disconnected_at=datetime.fromisoformat(data["disconnected_at"]),
            trigger_entity_id=data.get("trigger_entity_id", ""),
            area_name=data.get("area_name"),
            device_model=data.get("device_model"),
        )
        if data.get("reconnected_at"):
            evt.reconnected_at = datetime.fromisoformat(data["reconnected_at"])
        evt.included_in_summary = data.get("included_in_summary", False)
        return evt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_summary_time(time_str: str) -> tuple[int, int]:
    try:
        parts = str(time_str).split(":")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 8, 0


def _next_occurrence(now: datetime, hour: int, minute: int, day_ints: set[int]) -> datetime:
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    for _ in range(7):
        if candidate.weekday() in day_ints:
            return candidate
        candidate += timedelta(days=1)
    return now + timedelta(days=1)


def _repair_issue_id(device_key: str) -> str:
    return f"device_offline_{device_key}".replace(".", "_").replace("-", "_").replace(" ", "_")


def _build_extra_line(area_name: str | None, device_model: str | None) -> str:
    parts = [p for p in [area_name and f"📍 {area_name}", device_model] if p]
    return "  ·  ".join(parts)


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class ConnectionObserverCoordinator:

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
        self._events: list[DisconnectEvent] = []
        self._last_summary: datetime | None = None
        self._unsub: list[Callable] = []
        self._startup_complete = False
        self._pending_disconnects: dict[str, Callable] = {}
        self._last_notified: dict[str, datetime] = {}
        self._listeners: list[Callable[[], None]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def events(self) -> list[DisconnectEvent]:
        return self._events

    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        @callback
        def _remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _remove

    @callback
    def _async_notify_listeners(self) -> None:
        for listener in self._listeners:
            listener()

    async def async_send_summary_now(self) -> None:
        await self._send_summary()

    async def async_clear_history(self) -> None:
        for ev in self._events:
            if ev.reconnected_at is None:
                async_delete_issue(self.hass, DOMAIN, _repair_issue_id(ev.device_key))
        self._events.clear()
        self._last_summary = None
        await self._save_store()
        self._async_notify_listeners()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_setup(self) -> None:
        await self._load_store()
        self._setup_startup_guard()
        self._setup_state_listener()
        self._setup_summary_scheduler()
        self._setup_watchdog()

    async def async_unload(self) -> None:
        for cancel_fn in self._pending_disconnects.values():
            cancel_fn()
        self._pending_disconnects.clear()
        for unsub in self._unsub:
            unsub()
        self._unsub.clear()
        await self._save_store()

    async def async_update_options(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        for cancel_fn in self._pending_disconnects.values():
            cancel_fn()
        self._pending_disconnects.clear()
        for unsub in self._unsub:
            unsub()
        self._unsub.clear()
        self._startup_complete = True
        self._setup_state_listener()
        self._setup_summary_scheduler()
        self._setup_watchdog()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_startup_guard(self) -> None:
        if self.hass.state == CoreState.running:
            self._startup_complete = True
            return

        @callback
        def _on_ha_started(_event: Event) -> None:
            async_call_later(self.hass, STARTUP_GRACE_SECONDS, self._mark_startup_complete)

        self._unsub.append(
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_ha_started)
        )

    @callback
    def _mark_startup_complete(self, _now: Any) -> None:
        self._startup_complete = True
        _LOGGER.debug("Connection Observer: startup grace period ended, tracking active")

    def _setup_state_listener(self) -> None:
        self._unsub.append(
            self.hass.bus.async_listen("state_changed", self._handle_state_change)
        )

    def _setup_summary_scheduler(self) -> None:
        if self._cfg.get(CONF_NOTIFY_SUMMARY):
            self._schedule_next_summary()

    def _schedule_next_summary(self) -> None:
        if not self._cfg.get(CONF_NOTIFY_SUMMARY):
            return
        hour, minute = _parse_summary_time(self._cfg.get(CONF_SUMMARY_TIME, "08:00"))
        days: list[str] = self._cfg.get(CONF_SUMMARY_DAYS, [str(i) for i in range(7)])
        day_ints = {int(d) for d in days}
        next_run = _next_occurrence(dt_util.now(), hour, minute, day_ints)
        _LOGGER.debug("Connection Observer: next summary at %s", next_run)

        @callback
        def _fire(_now: datetime) -> None:
            self.hass.async_create_task(self._run_summary_and_reschedule())

        self._unsub.append(async_track_point_in_time(self.hass, _fire, next_run))

    async def _run_summary_and_reschedule(self) -> None:
        try:
            await self._send_summary()
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Connection Observer: error in summary")
        finally:
            self._schedule_next_summary()

    def _setup_watchdog(self) -> None:
        self._unsub.append(
            async_track_time_interval(
                self.hass,
                lambda _now: self.hass.async_create_task(self._run_watchdog()),
                timedelta(seconds=WATCHDOG_INTERVAL_SECONDS),
            )
        )

    # ------------------------------------------------------------------
    # State change
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
        if entity_id in self._cfg.get(CONF_EXCLUDED_ENTITIES, []):
            return
        protocol = self._get_entity_protocol(entity_id)
        if not protocol or protocol not in self._cfg.get(CONF_PROTOCOLS, []):
            return
        going_unavailable = (
            new_state.state == "unavailable" and old_state.state != "unavailable"
        )
        coming_back = (
            old_state.state == "unavailable" and new_state.state != "unavailable"
        )
        if going_unavailable:
            self._on_disconnect(entity_id, protocol)
        elif coming_back:
            self._on_reconnect(entity_id)

    @callback
    def _on_disconnect(self, entity_id: str, protocol: str) -> None:
        device_key, device_name = self._resolve_device(entity_id)
        for ev in self._events:
            if ev.device_key == device_key and ev.reconnected_at is None and not ev.included_in_summary:
                return
        if device_key in self._pending_disconnects:
            return
        alert_delay = int(self._cfg.get(CONF_ALERT_DELAY, 0))
        if alert_delay > 0:
            @callback
            def _confirm(_now: Any, _eid: str = entity_id, _dk: str = device_key,
                         _dn: str = device_name, _proto: str = protocol) -> None:
                self._pending_disconnects.pop(_dk, None)
                state = self.hass.states.get(_eid)
                if state and state.state == "unavailable":
                    self._create_event(_dk, _dn, _eid, _proto)
            cancel = async_call_later(self.hass, alert_delay * 60, _confirm)
            self._pending_disconnects[device_key] = cancel
        else:
            self._create_event(device_key, device_name, entity_id, protocol)

    @callback
    def _on_reconnect(self, entity_id: str) -> None:
        device_key, _ = self._resolve_device(entity_id)
        cancel_fn = self._pending_disconnects.pop(device_key, None)
        if cancel_fn:
            cancel_fn()
            return
        now = dt_util.now()
        changed = False
        device_name = device_key
        for ev in self._events:
            if ev.device_key == device_key and ev.reconnected_at is None:
                ev.reconnected_at = now
                device_name = ev.device_name
                changed = True
                async_delete_issue(self.hass, DOMAIN, _repair_issue_id(device_key))
                _LOGGER.info("Connection Observer: %s is back online", ev.device_name)
                break
        if changed:
            self._async_notify_listeners()
            self.hass.async_create_task(self._save_store())
            if self._cfg.get(CONF_NOTIFY_RECONNECT):
                self.hass.async_create_task(self._send_reconnect(device_name))

    @callback
    def _create_event(self, device_key: str, device_name: str, entity_id: str, protocol: str) -> None:
        area_name = self._get_area_name(entity_id) if self._cfg.get(CONF_INCLUDE_AREA) else None
        device_model = self._get_device_model(entity_id) if self._cfg.get(CONF_INCLUDE_DEVICE_INFO) else None
        evt = DisconnectEvent(
            device_key=device_key,
            device_name=device_name,
            protocol=protocol,
            disconnected_at=dt_util.now(),
            trigger_entity_id=entity_id,
            area_name=area_name,
            device_model=device_model,
        )
        self._events.append(evt)
        _LOGGER.info("Connection Observer: %s (%s) went offline", device_name, protocol)
        self._async_notify_listeners()
        self.hass.async_create_task(self._save_store())
        if self._cfg.get(CONF_NOTIFY_IMMEDIATE):
            cooldown = int(self._cfg.get(CONF_COOLDOWN, 0))
            if cooldown > 0:
                last = self._last_notified.get(device_key)
                if last and (dt_util.now() - last).total_seconds() < cooldown * 60:
                    return
            self._last_notified[device_key] = dt_util.now()
            self.hass.async_create_task(self._send_immediate(evt))

    # ------------------------------------------------------------------
    # Watchdog
    # ------------------------------------------------------------------

    async def _run_watchdog(self) -> None:
        changed = False
        repairs_hours = int(self._cfg.get(CONF_REPAIRS_THRESHOLD, 24))

        for ev in self._events:
            if ev.reconnected_at is not None:
                # Closed event – make sure repair issue is gone
                async_delete_issue(self.hass, DOMAIN, _repair_issue_id(ev.device_key))
                continue

            # Check if device actually came back (missed state_changed)
            if ev.trigger_entity_id:
                state = self.hass.states.get(ev.trigger_entity_id)
                if state is not None and state.state != "unavailable":
                    _LOGGER.debug("Watchdog: %s recovered (missed event)", ev.device_name)
                    ev.reconnected_at = dt_util.now()
                    changed = True
                    async_delete_issue(self.hass, DOMAIN, _repair_issue_id(ev.device_key))
                    if self._cfg.get(CONF_NOTIFY_RECONNECT):
                        self.hass.async_create_task(self._send_reconnect(ev.device_name))
                    continue

            # Create HA Repairs entry if offline long enough
            if repairs_hours > 0:
                offline_duration = dt_util.now() - ev.disconnected_at
                if offline_duration >= timedelta(hours=repairs_hours):
                    since_str = ev.disconnected_at.strftime("%Y-%m-%d %H:%M")
                    async_create_issue(
                        self.hass,
                        DOMAIN,
                        _repair_issue_id(ev.device_key),
                        is_fixable=False,
                        severity=IssueSeverity.WARNING,
                        translation_key="device_offline",
                        translation_placeholders={
                            "device_name": ev.device_name,
                            "protocol": ev.protocol,
                            "since": since_str,
                        },
                    )

        if changed:
            self._async_notify_listeners()
            await self._save_store()

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def _msg(self, key: str, **kwargs: Any) -> str:
        """Return a notification string: custom template if set, else language default."""
        tmpl_conf_key = f"tmpl_{key}"
        tmpl = self._cfg.get(tmpl_conf_key, "").strip()
        lang = self._cfg.get(CONF_LANGUAGE, "en")
        base = tmpl if tmpl else _MESSAGES.get(lang, _MESSAGES["en"]).get(
            key, _MESSAGES["en"].get(key, "")
        )
        try:
            return base.format_map(kwargs)
        except (KeyError, ValueError):
            _LOGGER.warning("Connection Observer: template error in '%s': %s", key, base)
            return base

    async def _send_immediate(self, evt: DisconnectEvent) -> None:
        services = self._notify_services()
        if not services:
            return
        time_str = evt.disconnected_at.strftime("%H:%M")
        area = f" [{evt.area_name}]" if evt.area_name else ""
        model = evt.device_model or ""

        title = self._msg(
            "imm_title",
            device_name=evt.device_name, protocol=evt.protocol,
            time=time_str, area=area, model=model,
        )
        # If user has a custom message template, use it; otherwise add extra line
        if self._cfg.get(CONF_TMPL_IMM_MSG, "").strip():
            msg = self._msg(
                "imm_msg",
                device_name=evt.device_name, protocol=evt.protocol,
                time=time_str, area=area, model=model,
            )
        else:
            lang = self._cfg.get(CONF_LANGUAGE, "en")
            msg = _MESSAGES.get(lang, _MESSAGES["en"])["imm_msg"].format(
                device_name=evt.device_name, protocol=evt.protocol, time=time_str,
                area=area, model=model,
            )
            extra = _build_extra_line(evt.area_name, evt.device_model)
            if extra:
                msg += f"\n{extra}"

        await self._notify_all(services, title, msg)

    async def _send_reconnect(self, device_name: str) -> None:
        services = self._notify_services()
        if not services:
            return
        title = self._msg("rec_title", device_name=device_name)
        msg = self._msg("rec_msg", device_name=device_name)
        await self._notify_all(services, title, msg)

    async def _send_summary(self) -> None:
        services = self._notify_services()
        if not services:
            return
        pending_all = [ev for ev in self._events if not ev.included_in_summary]
        if not pending_all:
            return

        min_dur_min = int(self._cfg.get(CONF_MIN_OFFLINE_DURATION, 0))
        if min_dur_min > 0:
            threshold = timedelta(minutes=min_dur_min)
            now = dt_util.now()
            pending_report = [
                ev for ev in pending_all
                if (ev.reconnected_at or now) - ev.disconnected_at >= threshold
            ]
        else:
            pending_report = pending_all

        # Mark everything (incl. short blips) as processed
        for ev in pending_all:
            ev.included_in_summary = True
        self._last_summary = dt_util.now()

        if not pending_report:
            await self._save_store()
            return

        lang = self._cfg.get(CONF_LANGUAGE, "en")
        # Date format varies by language
        dt_fmt = "%d.%m. %H:%M" if lang == "de" else "%m/%d %H:%M"

        title = self._msg("sum_title", count=len(pending_report))
        header = self._msg("sum_header", count=len(pending_report))
        lines = [header]

        for ev in pending_report:
            area = f" [{ev.area_name}]" if ev.area_name else ""
            t_off = ev.disconnected_at.strftime(dt_fmt)
            if ev.reconnected_at:
                t_on = ev.reconnected_at.strftime("%H:%M")
                lines.append(self._msg(
                    "sum_resolved",
                    device_name=ev.device_name, area=area, protocol=ev.protocol,
                    time_offline=t_off, time_online=t_on,
                ))
            else:
                lines.append(self._msg(
                    "sum_ongoing",
                    device_name=ev.device_name, area=area, protocol=ev.protocol,
                    time_offline=t_off,
                ))

        await self._notify_all(services, title, "\n".join(lines))
        await self._save_store()
        self._async_notify_listeners()

    # ------------------------------------------------------------------
    # Notification helpers
    # ------------------------------------------------------------------

    def _notify_services(self) -> list[str]:
        raw = self._cfg.get(CONF_NOTIFY_SERVICE, [])
        if isinstance(raw, str):
            return [raw] if raw else []
        return [s for s in raw if s]

    async def _notify_all(self, services: list[str], title: str, message: str) -> None:
        for service in services:
            await self._notify_one(service, title, message)

    async def _notify_one(self, service: str, title: str, message: str) -> None:
        parts = service.split(".", 1)
        if len(parts) != 2:
            _LOGGER.error("Connection Observer: invalid notify service: %s", service)
            return
        domain, service_name = parts
        try:
            await self.hass.services.async_call(
                domain, service_name, {"title": title, "message": message}, blocking=False
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Connection Observer: notification failed via %s: %s", service, err)

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------

    @property
    def _cfg(self) -> dict[str, Any]:
        return {**self.entry.data, **self.entry.options}

    def _get_entity_protocol(self, entity_id: str) -> str | None:
        er = async_get_entity_registry(self.hass)
        entry = er.async_get(entity_id)
        return entry.platform if entry else None

    def _resolve_device(self, entity_id: str) -> tuple[str, str]:
        er = async_get_entity_registry(self.hass)
        dr = async_get_device_registry(self.hass)
        entity_entry = er.async_get(entity_id)
        if entity_entry and entity_entry.device_id:
            device = dr.async_get(entity_entry.device_id)
            if device:
                return device.id, device.name_by_user or device.name or entity_id
        state = self.hass.states.get(entity_id)
        name = state.attributes.get("friendly_name", entity_id) if state else entity_id
        return entity_id, name

    def _get_area_name(self, entity_id: str) -> str | None:
        er = async_get_entity_registry(self.hass)
        dr = async_get_device_registry(self.hass)
        ar = async_get_area_registry(self.hass)
        entity_entry = er.async_get(entity_id)
        if not entity_entry:
            return None
        area_id = entity_entry.area_id
        if not area_id and entity_entry.device_id:
            device = dr.async_get(entity_entry.device_id)
            if device:
                area_id = device.area_id
        if area_id:
            area = ar.async_get_area(area_id)
            if area:
                return area.name
        return None

    def _get_device_model(self, entity_id: str) -> str | None:
        er = async_get_entity_registry(self.hass)
        dr = async_get_device_registry(self.hass)
        entity_entry = er.async_get(entity_id)
        if entity_entry and entity_entry.device_id:
            device = dr.async_get(entity_entry.device_id)
            if device:
                parts = [p for p in [device.manufacturer, device.model] if p]
                return " – ".join(parts) if parts else None
        return None

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
