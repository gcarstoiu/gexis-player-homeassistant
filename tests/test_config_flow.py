"""Adding a player: by its address, or found on the network and confirmed."""

from __future__ import annotations

from collections.abc import Generator
from ipaddress import ip_address
from unittest.mock import patch

import aiohttp
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from custom_components.gexis.const import DOMAIN

from .conftest import BASE, HOST, STATUS


@pytest.fixture(autouse=True)
def no_setup() -> Generator[None]:
    """A flow's test ends at the entry; setting it up is the other tests'."""
    with patch("custom_components.gexis.async_setup_entry", return_value=True):
        yield


def discovery(address: str = HOST) -> ZeroconfServiceInfo:
    return ZeroconfServiceInfo(
        ip_address=ip_address(address),
        ip_addresses=[ip_address(address)],
        hostname="livingroom.local.",
        name="livingroom._gexis._tcp.local.",
        port=8090,
        type="_gexis._tcp.local.",
        properties={},
    )


async def test_a_player_added_by_its_address(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{BASE}/player/status", json=STATUS)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": HOST, "port": 8090})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room"
    assert result["data"] == {"host": HOST, "port": 8090}
    assert result["result"].unique_id == STATUS["id"]


async def test_an_address_that_does_not_answer_says_so(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{BASE}/player/status", exc=aiohttp.ClientError)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": HOST, "port": 8090})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_a_player_without_a_lasting_id_is_asked_to_update(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{BASE}/player/status", json={k: v for k, v in STATUS.items() if k != "id"})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": HOST, "port": 8090})
    assert result["errors"] == {"base": "update_player"}


async def test_a_player_found_on_the_network_is_added_once_confirmed(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{BASE}/player/status", json=STATUS)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=discovery()
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"host": HOST, "port": 8090}


async def test_a_known_player_at_a_new_address_is_followed(hass: HomeAssistant, aioclient_mock, entry) -> None:
    entry.add_to_hass(hass)
    aioclient_mock.get("http://192.0.2.11:8090/player/status", json=STATUS)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=discovery("192.0.2.11")
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == "192.0.2.11"


async def test_an_old_player_found_on_the_network_is_not_offered(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{BASE}/player/status", json={k: v for k, v in STATUS.items() if k != "id"})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=discovery()
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "update_player"
