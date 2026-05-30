"""Config flow and options flow for Connection Observer."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ALERT_DELAY,
    CONF_COOLDOWN,
    CONF_EXCLUDED_DEVICES,
    CONF_EXCLUDED_DOMAINS,
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
    KNOWN_PROTOCOLS,
    LANG_DE,
    LANG_EN,
    LANG_ES,
    LANG_FR,
    LANG_NL,
    PROTOCOL_DELAY_HINTS,
)

_LOGGER = logging.getLogger(__name__)

_WEEKDAY_OPTIONS = [
    selector.SelectOptionDict(value="0", label="Monday / Montag"),
    selector.SelectOptionDict(value="1", label="Tuesday / Dienstag"),
    selector.SelectOptionDict(value="2", label="Wednesday / Mittwoch"),
    selector.SelectOptionDict(value="3", label="Thursday / Donnerstag"),
    selector.SelectOptionDict(value="4", label="Friday / Freitag"),
    selector.SelectOptionDict(value="5", label="Saturday / Samstag"),
    selector.SelectOptionDict(value="6", label="Sunday / Sonntag"),
]

_LANGUAGE_OPTIONS = [
    selector.SelectOptionDict(value=LANG_EN, label="English"),
    selector.SelectOptionDict(value=LANG_DE, label="Deutsch"),
    selector.SelectOptionDict(value=LANG_FR, label="Français"),
    selector.SelectOptionDict(value=LANG_NL, label="Nederlands"),
    selector.SelectOptionDict(value=LANG_ES, label="Español"),
]

_DEFAULT_DAYS = [str(i) for i in range(7)]

_MINUTES_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0,
        max=1440,
        step=1,
        unit_of_measurement="min",
        mode=selector.NumberSelectorMode.BOX,
    )
)

_HOURS_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0,
        max=168,
        step=1,
        unit_of_measurement="h",
        mode=selector.NumberSelectorMode.BOX,
    )
)

_TEXT_SELECTOR = selector.TextSelector(
    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
)

_DOMAIN_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[
            selector.SelectOptionDict(value="sensor", label="sensor"),
            selector.SelectOptionDict(value="binary_sensor", label="binary_sensor"),
            selector.SelectOptionDict(value="button", label="button"),
            selector.SelectOptionDict(value="event", label="event"),
            selector.SelectOptionDict(value="number", label="number"),
            selector.SelectOptionDict(value="select", label="select"),
            selector.SelectOptionDict(value="text", label="text"),
            selector.SelectOptionDict(value="update", label="update"),
        ],
        multiple=True,
        custom_value=True,
    )
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _available_protocols(hass) -> dict[str, str]:
    found: dict[str, str] = {}
    for entry in hass.config_entries.async_entries():
        if entry.domain in KNOWN_PROTOCOLS and entry.domain not in found:
            found[entry.domain] = KNOWN_PROTOCOLS[entry.domain]
    return found


def _available_notify_services(hass) -> list[str]:
    return sorted(
        f"notify.{name}"
        for name in hass.services.async_services().get("notify", {})
    )


def _protocol_selector(protocols: dict[str, str]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=k, label=v)
                for k, v in protocols.items()
            ],
            multiple=True,
        )
    )


def _notify_selector(services: list[str]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[selector.SelectOptionDict(value=s, label=s) for s in services],
            multiple=True,
            custom_value=True,
        )
    )


def _build_expert_schema(
    selected_protocols: list[str],
    current_delays: dict[str, int],
    watch_label: str,
) -> vol.Schema:
    """Build the dynamic expert-step schema.

    Per-protocol delay fields are named ``delay_<protocol>``.
    A value of 0 means "use the global alert delay".  Positive values
    override the global delay for that specific protocol.
    """
    schema_dict: dict[Any, Any] = {
        vol.Optional("apply_recommendations", default=False): selector.BooleanSelector(),
    }
    for proto in selected_protocols:
        key = f"delay_{proto}"
        default_val = current_delays.get(proto, 0)
        schema_dict[vol.Optional(key, default=default_val)] = _MINUTES_SELECTOR
    schema_dict[vol.Optional(CONF_WATCH_LABEL, default=watch_label)] = _TEXT_SELECTOR
    return vol.Schema(schema_dict)


def _parse_protocol_delays(
    user_input: dict[str, Any],
    selected_protocols: list[str],
) -> dict[str, int]:
    """Extract per-protocol delays from form data.

    Only protocols with a value > 0 are stored; 0 means "use global delay"
    and is therefore omitted from the returned dict.
    """
    delays: dict[str, int] = {}
    for proto in selected_protocols:
        raw = user_input.get(f"delay_{proto}", 0)
        val = int(raw or 0)
        if val > 0:
            delays[proto] = val
    return delays


# ---------------------------------------------------------------------------
# Config flow  (5 steps: protocols → notifications → test → advanced → expert)
# ---------------------------------------------------------------------------

class ConnectionObserverConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    _data: dict[str, Any]

    def __init__(self) -> None:
        self._data = {}

    # Step 1 – protocols + language
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        protocols = _available_protocols(self.hass)
        if not protocols:
            return self.async_abort(reason="no_protocols")

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notifications()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PROTOCOLS): _protocol_selector(protocols),
                    vol.Required(CONF_LANGUAGE, default=LANG_EN): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=_LANGUAGE_OPTIONS)
                    ),
                }
            ),
        )

    # Step 2 – notification services + modes
    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_test()

        notify_services = _available_notify_services(self.hass)
        return self.async_show_form(
            step_id="notifications",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NOTIFY_SERVICE): _notify_selector(notify_services),
                    vol.Optional(CONF_NOTIFY_IMMEDIATE, default=False): selector.BooleanSelector(),
                    vol.Optional(CONF_NOTIFY_SUMMARY, default=True): selector.BooleanSelector(),
                    vol.Optional(CONF_SUMMARY_TIME, default="08:00:00"): selector.TimeSelector(),
                    vol.Optional(CONF_SUMMARY_DAYS, default=_DEFAULT_DAYS): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=_WEEKDAY_OPTIONS,
                            multiple=True,
                        )
                    ),
                    vol.Optional(CONF_NOTIFY_RECONNECT, default=False): selector.BooleanSelector(),
                }
            ),
        )

    # Step 3 – test notification
    async def async_step_test(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get("send_test", True):
                services = self._data.get(CONF_NOTIFY_SERVICE, [])
                if isinstance(services, str):
                    services = [services] if services else []
                failed: list[str] = []
                for svc in services:
                    try:
                        domain, service_name = svc.split(".", 1)
                        await self.hass.services.async_call(
                            domain,
                            service_name,
                            {
                                "title": "Connection Observer – Test",
                                "message": (
                                    "✅ Test notification from Connection Observer. "
                                    "Your notification service is working correctly!"
                                ),
                            },
                            blocking=True,
                        )
                    except Exception as exc:  # noqa: BLE001
                        _LOGGER.warning(
                            "Connection Observer: test notification failed via %s: %s", svc, exc
                        )
                        failed.append(svc)

                if failed:
                    errors["base"] = "test_failed"
                    return self.async_show_form(
                        step_id="test",
                        data_schema=vol.Schema(
                            {vol.Optional("send_test", default=True): selector.BooleanSelector()}
                        ),
                        errors=errors,
                    )

            return await self.async_step_advanced()

        return self.async_show_form(
            step_id="test",
            data_schema=vol.Schema(
                {vol.Optional("send_test", default=True): selector.BooleanSelector()}
            ),
        )

    # Step 4 – advanced / opt-in features
    async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_expert()

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_ALERT_DELAY, default=0): _MINUTES_SELECTOR,
                    vol.Optional(CONF_COOLDOWN, default=0): _MINUTES_SELECTOR,
                    vol.Optional(CONF_MIN_OFFLINE_DURATION, default=0): _MINUTES_SELECTOR,
                    vol.Optional(CONF_INCLUDE_AREA, default=False): selector.BooleanSelector(),
                    vol.Optional(CONF_INCLUDE_DEVICE_INFO, default=False): selector.BooleanSelector(),
                    vol.Optional(CONF_EXCLUDED_DOMAINS, default=[]): _DOMAIN_SELECTOR,
                    vol.Optional(CONF_EXCLUDED_DEVICES, default=[]): selector.DeviceSelector(
                        selector.DeviceSelectorConfig(multiple=True)
                    ),
                }
            ),
        )

    # Step 5 – expert: per-protocol delays + watch label
    async def async_step_expert(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        selected_protocols: list[str] = self._data.get(CONF_PROTOCOLS, [])
        current_delays: dict[str, int] = {}
        watch_label: str = ""

        if user_input is not None:
            # If the user clicked "Apply recommended delays", pre-fill and re-render
            if user_input.get("apply_recommendations"):
                pre_delays = {p: PROTOCOL_DELAY_HINTS[p] for p in selected_protocols if p in PROTOCOL_DELAY_HINTS}
                return self.async_show_form(
                    step_id="expert",
                    data_schema=_build_expert_schema(
                        selected_protocols,
                        pre_delays,
                        user_input.get(CONF_WATCH_LABEL, ""),
                    ),
                )

            # Normal submission – parse delays and finish
            protocol_delays = _parse_protocol_delays(user_input, selected_protocols)
            self._data[CONF_PROTOCOL_DELAYS] = protocol_delays
            self._data[CONF_WATCH_LABEL] = user_input.get(CONF_WATCH_LABEL, "").strip()
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Connection Observer", data=self._data)

        return self.async_show_form(
            step_id="expert",
            data_schema=_build_expert_schema(selected_protocols, current_delays, watch_label),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "ConnectionObserverOptionsFlow":
        return ConnectionObserverOptionsFlow(config_entry)


# ---------------------------------------------------------------------------
# Options flow  (6 steps: protocols → notifications → advanced → expert → templates → test)
# ---------------------------------------------------------------------------

class ConnectionObserverOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._data: dict[str, Any] = {}

    def _cur(self) -> dict[str, Any]:
        """Merged current config (data + options) as single dict."""
        return {**self._entry.data, **self._entry.options}

    # Step 1 – protocols + language
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notifications()

        cur = self._cur()
        protocols = _available_protocols(self.hass)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PROTOCOLS, default=cur.get(CONF_PROTOCOLS, [])
                    ): _protocol_selector(protocols),
                    vol.Required(
                        CONF_LANGUAGE, default=cur.get(CONF_LANGUAGE, LANG_EN)
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=_LANGUAGE_OPTIONS)
                    ),
                }
            ),
        )

    # Step 2 – notifications
    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_advanced()

        cur = self._cur()
        notify_services = _available_notify_services(self.hass)
        return self.async_show_form(
            step_id="notifications",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NOTIFY_SERVICE, default=cur.get(CONF_NOTIFY_SERVICE, [])
                    ): _notify_selector(notify_services),
                    vol.Optional(
                        CONF_NOTIFY_IMMEDIATE,
                        default=cur.get(CONF_NOTIFY_IMMEDIATE, False),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_NOTIFY_SUMMARY,
                        default=cur.get(CONF_NOTIFY_SUMMARY, True),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_SUMMARY_TIME,
                        default=cur.get(CONF_SUMMARY_TIME, "08:00:00"),
                    ): selector.TimeSelector(),
                    vol.Optional(
                        CONF_SUMMARY_DAYS,
                        default=cur.get(CONF_SUMMARY_DAYS, _DEFAULT_DAYS),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=_WEEKDAY_OPTIONS,
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        CONF_NOTIFY_RECONNECT,
                        default=cur.get(CONF_NOTIFY_RECONNECT, False),
                    ): selector.BooleanSelector(),
                }
            ),
        )

    # Step 3 – advanced timing + filters
    async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_expert()

        cur = self._cur()
        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ALERT_DELAY,
                        default=cur.get(CONF_ALERT_DELAY, 0),
                    ): _MINUTES_SELECTOR,
                    vol.Optional(
                        CONF_COOLDOWN,
                        default=cur.get(CONF_COOLDOWN, 0),
                    ): _MINUTES_SELECTOR,
                    vol.Optional(
                        CONF_MIN_OFFLINE_DURATION,
                        default=cur.get(CONF_MIN_OFFLINE_DURATION, 0),
                    ): _MINUTES_SELECTOR,
                    vol.Optional(
                        CONF_INCLUDE_AREA,
                        default=cur.get(CONF_INCLUDE_AREA, False),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_INCLUDE_DEVICE_INFO,
                        default=cur.get(CONF_INCLUDE_DEVICE_INFO, False),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_EXCLUDED_DOMAINS,
                        default=cur.get(CONF_EXCLUDED_DOMAINS, []),
                    ): _DOMAIN_SELECTOR,
                    vol.Optional(
                        CONF_EXCLUDED_DEVICES,
                        default=cur.get(CONF_EXCLUDED_DEVICES, []),
                    ): selector.DeviceSelector(
                        selector.DeviceSelectorConfig(multiple=True)
                    ),
                    vol.Optional(
                        CONF_REPAIRS_THRESHOLD,
                        default=cur.get(CONF_REPAIRS_THRESHOLD, 24),
                    ): _HOURS_SELECTOR,
                }
            ),
        )

    # Step 4 – expert: per-protocol delays + watch label
    async def async_step_expert(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        cur = self._cur()
        selected_protocols: list[str] = self._data.get(CONF_PROTOCOLS, cur.get(CONF_PROTOCOLS, []))
        current_delays: dict[str, int] = cur.get(CONF_PROTOCOL_DELAYS, {})
        watch_label: str = cur.get(CONF_WATCH_LABEL, "")

        if user_input is not None:
            # If the user clicked "Apply recommended delays", pre-fill and re-render
            if user_input.get("apply_recommendations"):
                pre_delays = {p: PROTOCOL_DELAY_HINTS[p] for p in selected_protocols if p in PROTOCOL_DELAY_HINTS}
                return self.async_show_form(
                    step_id="expert",
                    data_schema=_build_expert_schema(
                        selected_protocols,
                        pre_delays,
                        user_input.get(CONF_WATCH_LABEL, watch_label),
                    ),
                )

            # Normal submission – parse delays and advance
            protocol_delays = _parse_protocol_delays(user_input, selected_protocols)
            self._data[CONF_PROTOCOL_DELAYS] = protocol_delays
            self._data[CONF_WATCH_LABEL] = user_input.get(CONF_WATCH_LABEL, "").strip()
            return await self.async_step_templates()

        return self.async_show_form(
            step_id="expert",
            data_schema=_build_expert_schema(selected_protocols, current_delays, watch_label),
        )

    # Step 5 – notification templates (empty = use language default)
    async def async_step_templates(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_test()

        cur = self._cur()
        return self.async_show_form(
            step_id="templates",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_TMPL_IMM_TITLE,
                        default=cur.get(CONF_TMPL_IMM_TITLE, ""),
                    ): _TEXT_SELECTOR,
                    vol.Optional(
                        CONF_TMPL_IMM_MSG,
                        default=cur.get(CONF_TMPL_IMM_MSG, ""),
                    ): _TEXT_SELECTOR,
                    vol.Optional(
                        CONF_TMPL_REC_TITLE,
                        default=cur.get(CONF_TMPL_REC_TITLE, ""),
                    ): _TEXT_SELECTOR,
                    vol.Optional(
                        CONF_TMPL_REC_MSG,
                        default=cur.get(CONF_TMPL_REC_MSG, ""),
                    ): _TEXT_SELECTOR,
                    vol.Optional(
                        CONF_TMPL_SUM_TITLE,
                        default=cur.get(CONF_TMPL_SUM_TITLE, ""),
                    ): _TEXT_SELECTOR,
                    vol.Optional(
                        CONF_TMPL_SUM_LINE_RESOLVED,
                        default=cur.get(CONF_TMPL_SUM_LINE_RESOLVED, ""),
                    ): _TEXT_SELECTOR,
                    vol.Optional(
                        CONF_TMPL_SUM_LINE_ONGOING,
                        default=cur.get(CONF_TMPL_SUM_LINE_ONGOING, ""),
                    ): _TEXT_SELECTOR,
                }
            ),
        )

    # Step 6 – optional test notification
    async def async_step_test(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get("send_test", False):
                services = self._data.get(CONF_NOTIFY_SERVICE, [])
                if isinstance(services, str):
                    services = [services] if services else []
                failed: list[str] = []
                for svc in services:
                    try:
                        domain, service_name = svc.split(".", 1)
                        await self.hass.services.async_call(
                            domain,
                            service_name,
                            {
                                "title": "Connection Observer – Test",
                                "message": (
                                    "✅ Test notification from Connection Observer. "
                                    "Your notification service is working correctly!"
                                ),
                            },
                            blocking=True,
                        )
                    except Exception as exc:  # noqa: BLE001
                        _LOGGER.warning(
                            "Connection Observer: test notification failed via %s: %s", svc, exc
                        )
                        failed.append(svc)
                if failed:
                    errors["base"] = "test_failed"
                    return self.async_show_form(
                        step_id="test",
                        data_schema=vol.Schema(
                            {vol.Optional("send_test", default=False): selector.BooleanSelector()}
                        ),
                        errors=errors,
                    )
            return self.async_create_entry(title="", data=self._data)

        return self.async_show_form(
            step_id="test",
            data_schema=vol.Schema(
                {vol.Optional("send_test", default=False): selector.BooleanSelector()}
            ),
        )
