"""Config flow and options flow for Connection Observer."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    DOMAIN,
    KNOWN_PROTOCOLS,
    LANG_DE,
    LANG_EN,
)

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
]

_DEFAULT_DAYS = [str(i) for i in range(7)]


def _available_protocols(hass) -> dict[str, str]:
    """Return protocols that are actually configured in this HA instance."""
    found: dict[str, str] = {}
    for entry in hass.config_entries.async_entries():
        if entry.domain in KNOWN_PROTOCOLS and entry.domain not in found:
            found[entry.domain] = KNOWN_PROTOCOLS[entry.domain]
    return found


def _available_notify_services(hass) -> list[str]:
    services = [
        f"notify.{name}"
        for name in hass.services.async_services().get("notify", {})
    ]
    return sorted(services)


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
            custom_value=True,
        )
    )


# ---------------------------------------------------------------------------
# Config flow (initial setup)
# ---------------------------------------------------------------------------

class ConnectionObserverConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Two-step config flow: protocols → notifications."""

    VERSION = 1
    _data: dict[str, Any]

    def __init__(self) -> None:
        self._data = {}

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

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._data.update(user_input)
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Connection Observer", data=self._data)

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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "ConnectionObserverOptionsFlow":
        return ConnectionObserverOptionsFlow(config_entry)


# ---------------------------------------------------------------------------
# Options flow (reconfigure after setup)
# ---------------------------------------------------------------------------

class ConnectionObserverOptionsFlow(config_entries.OptionsFlow):
    """Full reconfiguration via HA options UI."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        cur = {**self._entry.data, **self._entry.options}
        protocols = _available_protocols(self.hass)
        notify_services = _available_notify_services(self.hass)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PROTOCOLS, default=cur.get(CONF_PROTOCOLS, [])
                    ): _protocol_selector(protocols),
                    vol.Required(
                        CONF_NOTIFY_SERVICE, default=cur.get(CONF_NOTIFY_SERVICE)
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
                    vol.Required(
                        CONF_LANGUAGE, default=cur.get(CONF_LANGUAGE, LANG_EN)
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=_LANGUAGE_OPTIONS)
                    ),
                    vol.Optional(
                        CONF_EXCLUDED_ENTITIES,
                        default=cur.get(CONF_EXCLUDED_ENTITIES, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(multiple=True)
                    ),
                }
            ),
        )
