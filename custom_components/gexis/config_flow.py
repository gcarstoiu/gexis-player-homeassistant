"""Adding a player: found on the network and confirmed, or by its address."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import GexisError, GexisPlayer, TooOld
from .const import DEFAULT_PORT, DOMAIN


class GexisConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host = ""
        self._port = DEFAULT_PORT
        self._name = ""

    async def _status(self, host: str, port: int) -> dict[str, Any]:
        return await GexisPlayer(async_get_clientsession(self.hass), host, port).fetch_status()

    def _entry(self) -> ConfigFlowResult:
        return self.async_create_entry(title=self._name, data={CONF_HOST: self._host, CONF_PORT: self._port})

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            try:
                status = await self._status(host, port)
            except TooOld:
                errors["base"] = "update_player"
            except GexisError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(status["id"])
                self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})
                self._host, self._port, self._name = host, port, status.get("name") or host
                return self._entry()
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(int, vol.Range(1, 65535)),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        if discovery_info.ip_address.version != 4:
            return self.async_abort(reason="not_ipv4_address")
        host, port = str(discovery_info.ip_address), discovery_info.port or DEFAULT_PORT
        try:
            status = await self._status(host, port)
        except TooOld:
            return self.async_abort(reason="update_player")
        except GexisError:
            return self.async_abort(reason="cannot_connect")
        await self.async_set_unique_id(status["id"])
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})
        self._host, self._port, self._name = host, port, status.get("name") or host
        self.context["title_placeholders"] = {"name": self._name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self._entry()
        self._set_confirm_only()
        return self.async_show_form(step_id="zeroconf_confirm", description_placeholders={"name": self._name})
