"""Core coordinator for Connection Observer."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue, async_delete_issue
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
    CONF_EXCLUDED_DEVICES,
    CONF_EXCLUDED_DOMAINS,
    CONF_EXCLUDED_ENTITIES,
    CONF_INCLUDE_AREA,
    CONF_INCLUDE_DEVICE_INFO,
    CONF_LANGUAGE,
    CONF_MIN_OFFLINE_DURATION,
    CONF_NOTIFY_IMMEDIATE,
    CONF_NOTIFY_RECONNECT,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_SUMMARY,
    CONF_PROTOCOL_DELAYS,
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
    CONF_WATCH_LABEL,
    DOMAIN,
    LABEL_CRITICAL,
    LABEL_IGNORE,
    LABEL_WATCH,
    STARTUP_GRACE_SECONDS,
    STORAGE_KEY,
    STORAGE_VERSION,
    WATCHDOG_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

EVENT_RETENTION_DAYS = 30
FLOOD_THRESHOLD = 5          # devices within window → flood mode
FLOOD_COLLECT_SECONDS = 5    # collect window: wait this long before flushing the buffer

# Watch-label state sets: accept binary_sensor ("on"/"off") as well as template
# sensor variants ("True"/"False", "1"/"0") so users don't need to worry about
# whether they created a binary_sensor or a regular sensor template.
_WATCH_OFFLINE: frozenset[str] = frozenset({"on", "true", "1"})
_WATCH_ONLINE:  frozenset[str] = frozenset({"off", "false", "0"})

# ---------------------------------------------------------------------------
# Built-in message strings per language
# Variables available per key:
#   imm_title/msg      : {device_name} {protocol} {time} {area} {model}
#   rec_title/msg      : {device_name} {time}
#   sum_title          : {count}  (count = number of affected devices)
#   sum_resolved       : {device_name} {area} {protocol} {time_offline} {time_online}
#   sum_ongoing        : {device_name} {area} {protocol} {time_offline}
#   sum_multi_header   : {device_name} {area} {protocol} {count}  (header for devices with >1 event)
#   sum_sub_resolved   : {time_offline} {time_online}  (indented sub-line, resolved)
#   sum_sub_ongoing    : {time_offline}                (indented sub-line, still offline)
# {area} is pre-formatted as " [Room]" or "" — include it directly after {device_name}
# ---------------------------------------------------------------------------
_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "imm_title": "Connection Lost",
        "imm_msg": "⚠️ {device_name} ({protocol}) lost connection at {time}.",
        "rec_title": "Connection Restored",
        "rec_msg": "✅ {device_name} is back online.",
        "flood_dis_title": "Connection Outage – {count} devices",
        "flood_dis_msg": "⚠️ {count} devices went offline simultaneously — likely an infrastructure issue (e.g. router restart).\n{devices}",
        "flood_rec_title": "Connection Restored – {count} devices",
        "flood_rec_msg": "✅ {count} devices came back online:\n{devices}",
        "sum_title": "Connection Summary",
        "sum_header": "📋 {count} device(s) affected since last summary:",
        "sum_resolved": "• {device_name}{area} ({protocol}): offline since {time_offline}, back online at {time_online}",
        "sum_ongoing": "• {device_name}{area} ({protocol}): offline since {time_offline} ⚠️ still offline",
        "sum_multi_header": "• {device_name}{area} ({protocol}) – {count} event(s):",
        "sum_sub_resolved": "  ↓ {time_offline} → ✅ {time_online}",
        "sum_sub_ongoing": "  ↓ {time_offline} ⚠️ still offline",
        "sum_label_conflict": "⚠️ Label conflict: {device_name} has both observer_critical/observer_watch and observer_ignore — device is ignored.",
    },
    "de": {
        "imm_title": "Verbindungsabbruch",
        "imm_msg": "⚠️ {device_name} ({protocol}) hat um {time} die Verbindung verloren.",
        "rec_title": "Verbindung wiederhergestellt",
        "rec_msg": "✅ {device_name} ist wieder online.",
        "flood_dis_title": "Verbindungsausfall – {count} Geräte",
        "flood_dis_msg": "⚠️ {count} Geräte gleichzeitig offline — vermutlich ein Infrastruktur-Problem (z. B. Router-Neustart).\n{devices}",
        "flood_rec_title": "Verbindung wiederhergestellt – {count} Geräte",
        "flood_rec_msg": "✅ {count} Geräte wieder online:\n{devices}",
        "sum_title": "Verbindungs-Zusammenfassung",
        "sum_header": "📋 {count} Gerät(e) seit der letzten Zusammenfassung betroffen:",
        "sum_resolved": "• {device_name}{area} ({protocol}): offline seit {time_offline}, wieder online um {time_online}",
        "sum_ongoing": "• {device_name}{area} ({protocol}): offline seit {time_offline} ⚠️ noch offline",
        "sum_multi_header": "• {device_name}{area} ({protocol}) – {count} Ereignis(se):",
        "sum_sub_resolved": "  ↓ {time_offline} → ✅ {time_online}",
        "sum_sub_ongoing": "  ↓ {time_offline} ⚠️ noch offline",
        "sum_label_conflict": "⚠️ Labelkonflikt: {device_name} hat sowohl observer_critical/observer_watch als auch observer_ignore — Gerät wird ignoriert.",
    },
    "fr": {
        "imm_title": "Connexion perdue",
        "imm_msg": "⚠️ {device_name} ({protocol}) a perdu la connexion à {time}.",
        "rec_title": "Connexion rétablie",
        "rec_msg": "✅ {device_name} est de nouveau en ligne.",
        "flood_dis_title": "Panne de connexion – {count} appareils",
        "flood_dis_msg": "⚠️ {count} appareils hors ligne simultanément — probable problème d'infrastructure (ex. redémarrage du routeur).\n{devices}",
        "flood_rec_title": "Connexion rétablie – {count} appareils",
        "flood_rec_msg": "✅ {count} appareils de nouveau en ligne :\n{devices}",
        "sum_title": "Résumé des connexions",
        "sum_header": "📋 {count} appareil(s) affecté(s) depuis le dernier résumé :",
        "sum_resolved": "• {device_name}{area} ({protocol}) : hors ligne depuis {time_offline}, de nouveau en ligne à {time_online}",
        "sum_ongoing": "• {device_name}{area} ({protocol}) : hors ligne depuis {time_offline} ⚠️ toujours hors ligne",
        "sum_multi_header": "• {device_name}{area} ({protocol}) – {count} événement(s) :",
        "sum_sub_resolved": "  ↓ {time_offline} → ✅ {time_online}",
        "sum_sub_ongoing": "  ↓ {time_offline} ⚠️ toujours hors ligne",
        "sum_label_conflict": "⚠️ Conflit de labels : {device_name} a à la fois observer_critical/observer_watch et observer_ignore — l'appareil est ignoré.",
    },
    "nl": {
        "imm_title": "Verbinding verbroken",
        "imm_msg": "⚠️ {device_name} ({protocol}) heeft om {time} de verbinding verbroken.",
        "rec_title": "Verbinding hersteld",
        "rec_msg": "✅ {device_name} is weer online.",
        "flood_dis_title": "Verbindingsuitval – {count} apparaten",
        "flood_dis_msg": "⚠️ {count} apparaten tegelijk offline — waarschijnlijk een infrastructuurprobleem (bijv. router herstart).\n{devices}",
        "flood_rec_title": "Verbinding hersteld – {count} apparaten",
        "flood_rec_msg": "✅ {count} apparaten weer online:\n{devices}",
        "sum_title": "Verbindingsoverzicht",
        "sum_header": "📋 {count} apparaat/apparaten getroffen sinds het laatste overzicht:",
        "sum_resolved": "• {device_name}{area} ({protocol}): offline sinds {time_offline}, weer online om {time_online}",
        "sum_ongoing": "• {device_name}{area} ({protocol}): offline sinds {time_offline} ⚠️ nog steeds offline",
        "sum_multi_header": "• {device_name}{area} ({protocol}) – {count} gebeurtenis(sen):",
        "sum_sub_resolved": "  ↓ {time_offline} → ✅ {time_online}",
        "sum_sub_ongoing": "  ↓ {time_offline} ⚠️ nog steeds offline",
        "sum_label_conflict": "⚠️ Labelconflict: {device_name} heeft zowel observer_critical/observer_watch als observer_ignore — apparaat wordt genegeerd.",
    },
    "es": {
        "imm_title": "Conexión perdida",
        "imm_msg": "⚠️ {device_name} ({protocol}) perdió la conexión a las {time}.",
        "rec_title": "Conexión restaurada",
        "rec_msg": "✅ {device_name} está de nuevo en línea.",
        "flood_dis_title": "Fallo de conexión – {count} dispositivos",
        "flood_dis_msg": "⚠️ {count} dispositivos sin conexión simultáneamente — probable problema de infraestructura (p. ej. reinicio del router).\n{devices}",
        "flood_rec_title": "Conexión restaurada – {count} dispositivos",
        "flood_rec_msg": "✅ {count} dispositivos de nuevo en línea:\n{devices}",
        "sum_title": "Resumen de conexiones",
        "sum_header": "📋 {count} dispositivo(s) afectado(s) desde el último resumen:",
        "sum_resolved": "• {device_name}{area} ({protocol}): sin conexión desde {time_offline}, de nuevo en línea a las {time_online}",
        "sum_ongoing": "• {device_name}{area} ({protocol}): sin conexión desde {time_offline} ⚠️ todavía sin conexión",
        "sum_multi_header": "• {device_name}{area} ({protocol}) – {count} evento(s):",
        "sum_sub_resolved": "  ↓ {time_offline} → ✅ {time_online}",
        "sum_sub_ongoing": "  ↓ {time_offline} ⚠️ todavía sin conexión",
        "sum_label_conflict": "⚠️ Conflicto de etiquetas: {device_name} tiene tanto observer_critical/observer_watch como observer_ignore — el dispositivo se ignora.",
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
    is_critical: bool = False

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
            "is_critical": self.is_critical,
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
        evt.is_critical = data.get("is_critical", False)
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
        self._watch_label_entities: set[str] = set()
        self._active_repairs: set[str] = set()
        self._excluded_device_ids: set[str] = set()
        # Observer label caches (device_key → label)
        self._critical_device_ids: set[str] = set()
        self._watch_device_ids: set[str] = set()
        self._ignore_label_device_ids: set[str] = set()
        self._label_conflicts: set[str] = set()  # device_keys with conflicting labels
        # Flood detection buffers
        self._disconnect_flood_buffer: list[DisconnectEvent] = []
        self._disconnect_flood_unsub: Callable | None = None
        self._reconnect_flood_buffer: list[str] = []
        self._reconnect_flood_unsub: Callable | None = None

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

    async def async_clear_device(self, entity_id: str) -> None:
        device_key, _ = self._resolve_device(entity_id)
        async_delete_issue(self.hass, DOMAIN, _repair_issue_id(device_key))
        self._active_repairs.discard(device_key)
        before = len(self._events)
        self._events = [ev for ev in self._events if ev.device_key != device_key]
        if len(self._events) != before:
            await self._save_store()
            self._async_notify_listeners()
            _LOGGER.info("Connection Observer: cleared history for device %s", device_key)

    async def async_clear_history(self) -> None:
        for ev in self._events:
            if ev.reconnected_at is None:
                async_delete_issue(self.hass, DOMAIN, _repair_issue_id(ev.device_key))
                self._active_repairs.discard(ev.device_key)
        self._events.clear()
        self._last_summary = None
        await self._save_store()
        self._async_notify_listeners()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_setup(self) -> None:
        await self._load_store()
        await self._purge_stale_protocol_events()
        await self._maybe_catchup_summary()
        self._setup_startup_guard()
        self._setup_state_listener()
        self._setup_summary_scheduler()
        self._setup_watchdog()
        self._setup_watch_label_listener()
        self._refresh_excluded_devices()
        self._refresh_label_devices()
        await self._purge_excluded_events()

    async def async_unload(self) -> None:
        for cancel_fn in self._pending_disconnects.values():
            cancel_fn()
        self._pending_disconnects.clear()
        for unsub in self._unsub:
            unsub()
        self._unsub.clear()
        if self._disconnect_flood_unsub:
            self._disconnect_flood_unsub()
            self._disconnect_flood_unsub = None
        if self._reconnect_flood_unsub:
            self._reconnect_flood_unsub()
            self._reconnect_flood_unsub = None
        self._disconnect_flood_buffer.clear()
        self._reconnect_flood_buffer.clear()
        await self._save_store()

    async def async_update_options(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        for cancel_fn in self._pending_disconnects.values():
            cancel_fn()
        self._pending_disconnects.clear()
        for unsub in self._unsub:
            unsub()
        self._unsub.clear()
        self._startup_complete = True
        self._watch_label_entities.clear()
        self._excluded_device_ids.clear()
        self._critical_device_ids.clear()
        self._watch_device_ids.clear()
        self._ignore_label_device_ids.clear()
        self._label_conflicts.clear()
        self._setup_state_listener()
        self._setup_summary_scheduler()
        self._setup_watchdog()
        self._setup_watch_label_listener()
        self._refresh_excluded_devices()
        self._refresh_label_devices()
        await self._purge_excluded_events()
        await self._purge_stale_protocol_events()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_startup_guard(self) -> None:
        if self.hass.state == CoreState.running:
            self._startup_complete = True
            return

        @callback
        def _on_ha_started(_event: Event) -> None:
            # The one-time listener has fired; HA already removed it internally.
            # Remove the stale handle from _unsub so our cleanup loop doesn't try
            # to call it again, which would raise a ValueError in HA's core.
            if _unsub_handle in self._unsub:
                self._unsub.remove(_unsub_handle)
            async_call_later(self.hass, STARTUP_GRACE_SECONDS, self._mark_startup_complete)

        _unsub_handle = self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_ha_started)
        self._unsub.append(_unsub_handle)

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
        @callback
        def _watchdog_callback(_now: datetime) -> None:
            self.hass.async_create_task(self._run_watchdog())

        self._unsub.append(
            async_track_time_interval(
                self.hass,
                _watchdog_callback,
                timedelta(seconds=WATCHDOG_INTERVAL_SECONDS),
            )
        )

    def _refresh_watch_label_entities(self) -> None:
        """Scan entity registry for entities carrying the watch label and cache them.

        Comparison is case-insensitive so that label IDs stored in lower-case by
        HA (e.g. 'observer_watch') match whatever the user typed in the config
        field (e.g. 'Observer_watch').
        """
        label: str = self._cfg.get(CONF_WATCH_LABEL, "").strip()
        self._watch_label_entities.clear()
        if not label:
            return
        label_lower = label.lower()
        er = async_get_entity_registry(self.hass)
        for entry in er.entities.values():
            if any(lbl.lower() == label_lower for lbl in (entry.labels or set())):
                self._watch_label_entities.add(entry.entity_id)
        if self._watch_label_entities:
            _LOGGER.debug(
                "Connection Observer: watch-label '%s' matched %d entity/entities: %s",
                label, len(self._watch_label_entities), self._watch_label_entities,
            )

    def _setup_watch_label_listener(self) -> None:
        """Initial scan + subscribe to entity-registry changes to keep caches live.

        One listener handles both the watch-label entities and the observer label
        device caches so we don't register two separate subscribers.
        """
        self._refresh_watch_label_entities()
        self._refresh_label_devices()

        @callback
        def _on_registry_updated(_event: Event) -> None:
            self._refresh_watch_label_entities()
            self._refresh_label_devices()

        self._unsub.append(
            self.hass.bus.async_listen("entity_registry_updated", _on_registry_updated)
        )

    def _refresh_label_devices(self) -> None:
        """Scan the entity registry for observer labels and build device caches.

        Priority (highest first): observer_ignore > observer_critical > observer_watch.
        A device with both ignore and critical/watch is a conflict — observer_ignore wins
        and the conflict is recorded so it can appear as a warning in the summary.
        """
        self._critical_device_ids.clear()
        self._watch_device_ids.clear()
        self._ignore_label_device_ids.clear()
        self._label_conflicts.clear()

        er = async_get_entity_registry(self.hass)
        dr = async_get_device_registry(self.hass)

        critical: set[str] = set()
        watch: set[str] = set()
        ignore: set[str] = set()

        for entry in er.entities.values():
            labels = entry.labels or set()
            if not (labels & {LABEL_CRITICAL, LABEL_WATCH, LABEL_IGNORE}):
                continue
            if not entry.device_id:
                continue
            device = dr.async_get(entry.device_id)
            if not device:
                continue
            key = device.id
            if LABEL_CRITICAL in labels:
                critical.add(key)
            if LABEL_WATCH in labels:
                watch.add(key)
            if LABEL_IGNORE in labels:
                ignore.add(key)

        # Detect conflicts: ignore + (critical or watch) on the same device
        conflicts = ignore & (critical | watch)
        for key in conflicts:
            device = dr.async_get(key)
            name = (device.name_by_user or device.name or key) if device else key
            _LOGGER.warning(
                "Connection Observer: label conflict on '%s' — observer_ignore wins", name
            )

        self._label_conflicts = conflicts
        self._ignore_label_device_ids = ignore
        self._critical_device_ids = critical - ignore   # ignore wins
        self._watch_device_ids = watch - ignore - critical  # critical takes precedence

    def _refresh_excluded_devices(self) -> None:
        """Build a set of excluded device IDs from config.

        New configs store device IDs directly (CONF_EXCLUDED_DEVICES).
        Legacy configs stored entity IDs (CONF_EXCLUDED_ENTITIES) — those are
        migrated on the fly by resolving their device IDs.
        """
        self._excluded_device_ids.clear()
        # New: device IDs stored directly
        for device_id in self._cfg.get(CONF_EXCLUDED_DEVICES, []):
            self._excluded_device_ids.add(device_id)
        # Legacy migration: entity IDs → resolve to device IDs
        legacy: list[str] = self._cfg.get(CONF_EXCLUDED_ENTITIES, [])
        if legacy:
            er = async_get_entity_registry(self.hass)
            for eid in legacy:
                entry = er.async_get(eid)
                if entry and entry.device_id:
                    self._excluded_device_ids.add(entry.device_id)

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

        # ── Watch-label path ────────────────────────────────────────────────
        # Any entity labelled with CONF_WATCH_LABEL signals offline/online via
        # its state.  binary_sensor produces "on"/"off"; a template sensor may
        # produce "True"/"False" or "1"/"0" — all variants are accepted so that
        # users don't have to worry about the exact entity type.
        if entity_id in self._watch_label_entities:
            going_offline = (
                new_state.state.lower() in _WATCH_OFFLINE
                and old_state.state.lower() not in _WATCH_OFFLINE
            )
            coming_back = (
                new_state.state.lower() in _WATCH_ONLINE
                and old_state.state.lower() not in _WATCH_ONLINE
            )
            if going_offline:
                self._on_disconnect(entity_id, self._get_protocol_for_watch_entity(entity_id))
            elif coming_back:
                self._on_reconnect(entity_id)
            # Watch-label entities are handled exclusively here; skip normal flow.
            return

        # ── Normal unavailable-state path ───────────────────────────────────
        entity_domain = entity_id.split(".", 1)[0]
        if entity_domain == "device_tracker":
            return
        if entity_domain in self._cfg.get(CONF_EXCLUDED_DOMAINS, []):
            return

        # Resolve the device once for label + exclusion checks.
        er = async_get_entity_registry(self.hass)
        entry = er.async_get(entity_id)
        device_id = entry.device_id if entry else None

        # Device exclusion (config-based): skip all entities of an excluded device.
        if device_id and device_id in self._excluded_device_ids:
            return

        # Observer-label exclusion (observer_ignore beats everything).
        if device_id and device_id in self._ignore_label_device_ids:
            return

        protocol = self._get_entity_protocol(entity_id)
        configured_protocols: list[str] = self._cfg.get(CONF_PROTOCOLS, [])

        # Determine whether this entity's device is label-monitored and/or critical.
        is_critical = bool(device_id and device_id in self._critical_device_ids)
        is_label_watched = is_critical or bool(
            device_id and device_id in self._watch_device_ids
        )

        # Skip if neither protocol-monitored nor label-monitored.
        if not is_label_watched and (not protocol or protocol not in configured_protocols):
            return

        going_unavailable = (
            new_state.state == "unavailable" and old_state.state != "unavailable"
        )
        coming_back = (
            old_state.state == "unavailable" and new_state.state != "unavailable"
        )
        if going_unavailable:
            self._on_disconnect(entity_id, protocol or "unknown", is_critical=is_critical)
        elif coming_back:
            self._on_reconnect(entity_id)

    @callback
    def _on_disconnect(self, entity_id: str, protocol: str, is_critical: bool = False) -> None:
        device_key, device_name = self._resolve_device(entity_id)
        for ev in self._events:
            if ev.device_key == device_key and ev.reconnected_at is None and not ev.included_in_summary:
                return
        if device_key in self._pending_disconnects:
            return
        # Critical devices bypass alert delay entirely.
        protocol_delays: dict[str, int] = self._cfg.get(CONF_PROTOCOL_DELAYS, {})
        _proto_delay = protocol_delays.get(protocol)
        alert_delay = 0 if is_critical else int(
            _proto_delay if _proto_delay is not None else self._cfg.get(CONF_ALERT_DELAY, 0)
        )
        if alert_delay > 0:
            @callback
            def _confirm(_now: Any, _eid: str = entity_id, _dk: str = device_key,
                         _dn: str = device_name, _proto: str = protocol) -> None:
                self._pending_disconnects.pop(_dk, None)
                state = self.hass.states.get(_eid)
                if state:
                    is_watch = _eid in self._watch_label_entities
                    still_offline = (
                        state.state.lower() in _WATCH_OFFLINE
                        if is_watch
                        else state.state == "unavailable"
                    )
                    if still_offline:
                        self._create_event(_dk, _dn, _eid, _proto)
            cancel = async_call_later(self.hass, alert_delay * 60, _confirm)
            self._pending_disconnects[device_key] = cancel
        else:
            self._create_event(device_key, device_name, entity_id, protocol, is_critical=is_critical)

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
                self._active_repairs.discard(device_key)
                _LOGGER.info("Connection Observer: %s is back online", ev.device_name)
                break
        if changed:
            self._async_notify_listeners()
            self.hass.async_create_task(self._save_store())
            if self._cfg.get(CONF_NOTIFY_RECONNECT):
                self._buffer_reconnect_notification(device_name)

    @callback
    def _create_event(
        self,
        device_key: str,
        device_name: str,
        entity_id: str,
        protocol: str,
        is_critical: bool = False,
    ) -> None:
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
            is_critical=is_critical,
        )
        self._events.append(evt)
        _LOGGER.info(
            "Connection Observer: %s (%s) went offline%s",
            device_name, protocol, " [critical]" if is_critical else "",
        )
        self._async_notify_listeners()
        self.hass.async_create_task(self._save_store())
        # Critical devices always notify immediately (bypass CONF_NOTIFY_IMMEDIATE).
        if self._cfg.get(CONF_NOTIFY_IMMEDIATE) or is_critical:
            # Buffer the notification — flush after FLOOD_COLLECT_SECONDS.
            # Critical events are flushed immediately (not subject to flood grouping).
            if is_critical:
                self.hass.async_create_task(self._send_immediate(evt))
            else:
                self._disconnect_flood_buffer.append(evt)
                if self._disconnect_flood_unsub is None:
                    @callback
                    def _flush_dis(_now: Any) -> None:
                        self._disconnect_flood_unsub = None
                        self.hass.async_create_task(self._flush_disconnect_buffer())
                    self._disconnect_flood_unsub = async_call_later(
                        self.hass, FLOOD_COLLECT_SECONDS, _flush_dis
                    )

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
                self._active_repairs.discard(ev.device_key)
                continue

            # Check if device actually came back (missed state_changed)
            if ev.trigger_entity_id:
                state = self.hass.states.get(ev.trigger_entity_id)
                if state is None:
                    # Entity no longer exists (renamed or removed) – close silently
                    _LOGGER.debug("Watchdog: %s – trigger entity gone, closing event", ev.device_name)
                    ev.reconnected_at = dt_util.now()
                    changed = True
                    async_delete_issue(self.hass, DOMAIN, _repair_issue_id(ev.device_key))
                    self._active_repairs.discard(ev.device_key)
                    continue
                # Watch-label entities signal "back online" via off/false/0 (not "unavailable")
                is_watch = ev.trigger_entity_id in self._watch_label_entities
                recovered = (
                    state.state.lower() not in _WATCH_OFFLINE
                    if is_watch
                    else state.state != "unavailable"
                )
                if recovered:
                    _LOGGER.debug("Watchdog: %s recovered (missed event)", ev.device_name)
                    ev.reconnected_at = dt_util.now()
                    changed = True
                    async_delete_issue(self.hass, DOMAIN, _repair_issue_id(ev.device_key))
                    self._active_repairs.discard(ev.device_key)
                    if self._cfg.get(CONF_NOTIFY_RECONNECT):
                        self._buffer_reconnect_notification(ev.device_name)
                    continue

            # Create HA Repairs entry if offline long enough (only once per event)
            if repairs_hours > 0 and ev.device_key not in self._active_repairs:
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
                    self._active_repairs.add(ev.device_key)

        if changed:
            await self._save_store()

        # Always notify listeners when there are open events so that
        # the offline_duration attribute stays up to date in the sensor.
        has_open = any(ev.reconnected_at is None for ev in self._events)
        if changed or has_open:
            self._async_notify_listeners()

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Excluded-device cleanup (remove open events when a device is excluded)
    # ------------------------------------------------------------------

    async def _purge_excluded_events(self) -> None:
        """Remove open offline events for devices that are now excluded.

        Called after _refresh_excluded_devices() so that excluding an offline
        device immediately clears it from the offline list and HA Repairs.
        Pending disconnect timers for excluded devices are also cancelled.
        """
        if not self._excluded_device_ids:
            return
        # Cancel pending disconnect confirmations for excluded devices
        to_cancel = [
            dk for dk in list(self._pending_disconnects)
            if dk in self._excluded_device_ids
        ]
        for dk in to_cancel:
            cancel_fn = self._pending_disconnects.pop(dk)
            cancel_fn()
        # Remove open events and tidy up HA Repairs
        before = len(self._events)
        purged: list[str] = []
        kept: list[DisconnectEvent] = []
        for ev in self._events:
            if ev.reconnected_at is None and ev.device_key in self._excluded_device_ids:
                async_delete_issue(self.hass, DOMAIN, _repair_issue_id(ev.device_key))
                self._active_repairs.discard(ev.device_key)
                purged.append(ev.device_name)
            else:
                kept.append(ev)
        if len(kept) != before:
            self._events = kept
            await self._save_store()
            self._async_notify_listeners()
            _LOGGER.info(
                "Connection Observer: purged excluded device(s) from offline list: %s",
                ", ".join(purged),
            )

    async def _purge_stale_protocol_events(self) -> None:
        """Close open events for protocols that are no longer monitored.

        When a protocol is removed from the config its devices can never
        recover via state_changed, so they would linger as open events and
        generate stale HA Repairs entries indefinitely.  We remove them here
        so the offline list stays clean after a protocol reconfiguration.

        Watch-label events (protocol == "custom") are never purged — they are
        managed independently of the protocol list.
        """
        active_protocols: set[str] = set(self._cfg.get(CONF_PROTOCOLS, []))
        label_monitored = self._critical_device_ids | self._watch_device_ids
        kept: list[DisconnectEvent] = []
        purged: list[str] = []
        for ev in self._events:
            if (
                ev.reconnected_at is None
                and ev.protocol != "custom"
                and ev.protocol not in active_protocols
                and ev.device_key not in label_monitored  # keep label-monitored events
            ):
                async_delete_issue(self.hass, DOMAIN, _repair_issue_id(ev.device_key))
                self._active_repairs.discard(ev.device_key)
                purged.append(f"{ev.device_name} ({ev.protocol})")
            else:
                kept.append(ev)
        if purged:
            self._events = kept
            await self._save_store()
            self._async_notify_listeners()
            _LOGGER.info(
                "Connection Observer: removed %d stale event(s) for inactive protocol(s): %s",
                len(purged),
                ", ".join(purged),
            )

    # ------------------------------------------------------------------
    # Catch-up summary (missed scheduled time after reload/restart)
    # ------------------------------------------------------------------

    async def _maybe_catchup_summary(self) -> None:
        """Send the scheduled summary if it was missed today (e.g. after a config-entry reload)."""
        if not self._cfg.get(CONF_NOTIFY_SUMMARY):
            return
        hour, minute = _parse_summary_time(self._cfg.get(CONF_SUMMARY_TIME, "08:00"))
        days = {int(d) for d in self._cfg.get(CONF_SUMMARY_DAYS, [str(i) for i in range(7)])}
        now = dt_util.now()
        if now.weekday() not in days:
            return
        today_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now < today_at:
            return  # scheduled time not yet reached today
        if self._last_summary and self._last_summary >= today_at:
            return  # already sent today
        _LOGGER.debug("Connection Observer: catch-up summary (scheduled time was missed)")
        await self._send_summary()

    # ------------------------------------------------------------------
    # Flood detection helpers
    # ------------------------------------------------------------------

    @callback
    def _buffer_reconnect_notification(self, device_name: str) -> None:
        """Buffer a reconnect notification; send grouped if flood threshold is reached."""
        self._reconnect_flood_buffer.append(device_name)
        if self._reconnect_flood_unsub is None:
            @callback
            def _flush_rec(_now: Any) -> None:
                self._reconnect_flood_unsub = None
                self.hass.async_create_task(self._flush_reconnect_buffer())
            self._reconnect_flood_unsub = async_call_later(
                self.hass, FLOOD_COLLECT_SECONDS, _flush_rec
            )

    async def _flush_disconnect_buffer(self) -> None:
        """Flush buffered disconnect notifications: grouped if flood, individual otherwise."""
        buffer = self._disconnect_flood_buffer.copy()
        self._disconnect_flood_buffer.clear()
        if not buffer:
            return
        if len(buffer) >= FLOOD_THRESHOLD:
            await self._send_disconnect_flood(buffer)
        else:
            now = dt_util.now()
            cooldown = int(self._cfg.get(CONF_COOLDOWN, 0))
            for evt in buffer:
                if cooldown > 0:
                    last = self._last_notified.get(evt.device_key)
                    if last and (now - last).total_seconds() < cooldown * 60:
                        continue
                self._last_notified[evt.device_key] = now
                await self._send_immediate(evt)

    async def _send_disconnect_flood(self, events: list[DisconnectEvent]) -> None:
        """Send a single grouped notification for a flood of simultaneous disconnects."""
        services = self._notify_services()
        if not services:
            return
        count = len(events)
        device_list = "\n".join(
            f"• {ev.device_name} ({ev.protocol})" for ev in events
        )
        title = self._msg("flood_dis_title", count=count)
        msg = self._msg("flood_dis_msg", count=count, devices=device_list)
        await self._notify_all(services, title, msg)
        _LOGGER.info("Connection Observer: flood notification sent for %d devices", count)

    async def _flush_reconnect_buffer(self) -> None:
        """Flush buffered reconnect notifications: grouped if flood, individual otherwise."""
        buffer = self._reconnect_flood_buffer.copy()
        self._reconnect_flood_buffer.clear()
        if not buffer:
            return
        if len(buffer) >= FLOOD_THRESHOLD:
            await self._send_reconnect_flood(buffer)
        else:
            for device_name in buffer:
                await self._send_reconnect(device_name)

    async def _send_reconnect_flood(self, device_names: list[str]) -> None:
        """Send a single grouped notification for a flood of simultaneous reconnects."""
        services = self._notify_services()
        if not services:
            return
        count = len(device_names)
        device_list = "\n".join(f"• {name}" for name in device_names)
        title = self._msg("flood_rec_title", count=count)
        msg = self._msg("flood_rec_msg", count=count, devices=device_list)
        await self._notify_all(services, title, msg)
        _LOGGER.info("Connection Observer: flood reconnect notification sent for %d devices", count)

    # ------------------------------------------------------------------
    # Notification helpers
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

        # Group events by device, preserving first-seen order
        groups: dict[str, list] = {}
        for ev in pending_report:
            groups.setdefault(ev.device_key, []).append(ev)

        device_count = len(groups)
        title = self._msg("sum_title", count=device_count)
        header = self._msg("sum_header", count=device_count)
        lines = [header]

        for evts in groups.values():
            evts_sorted = sorted(evts, key=lambda e: e.disconnected_at)
            first = evts_sorted[0]
            area = f" [{first.area_name}]" if first.area_name else ""
            # Critical events replace the • bullet with 🔴.
            critical_flag = any(e.is_critical for e in evts_sorted)

            if len(evts_sorted) == 1:
                ev = evts_sorted[0]
                t_off = ev.disconnected_at.strftime(dt_fmt)
                if ev.reconnected_at:
                    t_on = ev.reconnected_at.strftime("%H:%M")
                    line = self._msg(
                        "sum_resolved",
                        device_name=ev.device_name, area=area, protocol=ev.protocol,
                        time_offline=t_off, time_online=t_on,
                    )
                else:
                    line = self._msg(
                        "sum_ongoing",
                        device_name=ev.device_name, area=area, protocol=ev.protocol,
                        time_offline=t_off,
                    )
                if critical_flag:
                    line = line.replace("• ", "🔴 ", 1)
                lines.append(line)
            else:
                # Multiple events — device header + indented sub-lines
                header_line = self._msg(
                    "sum_multi_header",
                    device_name=first.device_name, area=area, protocol=first.protocol,
                    count=len(evts_sorted),
                )
                if critical_flag:
                    header_line = header_line.replace("• ", "🔴 ", 1)
                lines.append(header_line)
                for ev in evts_sorted:
                    t_off = ev.disconnected_at.strftime(dt_fmt)
                    if ev.reconnected_at:
                        t_on = ev.reconnected_at.strftime("%H:%M")
                        lines.append(self._msg("sum_sub_resolved", time_offline=t_off, time_online=t_on))
                    else:
                        lines.append(self._msg("sum_sub_ongoing", time_offline=t_off))

        # Append label-conflict warnings if any conflicted devices had events this period
        if self._label_conflicts:
            dr = async_get_device_registry(self.hass)
            reported_keys = set(groups.keys())
            for device_key in self._label_conflicts & reported_keys:
                device = dr.async_get(device_key)
                name = (device.name_by_user or device.name or device_key) if device else device_key
                lines.append(self._msg("sum_label_conflict", device_name=name))

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

    def _get_protocol_for_watch_entity(self, entity_id: str) -> str:
        """Return the monitored protocol for the device that owns the watch-label entity.

        Looks up the device the watch-label entity belongs to, then searches all
        other entities on that device for one whose platform matches a monitored
        protocol.  Falls back to "custom" if no match is found.
        """
        try:
            monitored: list[str] = self._cfg.get(CONF_PROTOCOLS, [])
            er = async_get_entity_registry(self.hass)
            entry = er.async_get(entity_id)
            if not entry or not entry.device_id:
                return "custom"
            device_id = entry.device_id
            for e in er.entities.values():
                if e.device_id == device_id and e.platform in monitored:
                    return e.platform
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Connection Observer: could not resolve protocol for %s", entity_id)
        return "custom"

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
