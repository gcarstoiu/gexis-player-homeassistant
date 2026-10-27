"""The equaliser's setting (ADR-0163 16)."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from .conftest import BASE
from .test_media_player import setup

ENTITY = "select.living_room_equaliser_setting"


def equaliser(sel: str = "rock", on: bool = True) -> dict[str, Any]:
    return {
        "on": on,
        "sel": sel,
        "presets": [{"key": "flat", "name": "Flat"}, {"key": "rock", "name": "Rock"}],
        "own": [{"key": "u1", "name": "Evening"}],
    }


def puts(aioclient_mock) -> list[tuple[str, object]]:
    return [(str(url), body) for method, url, body, _ in aioclient_mock.mock_calls if method == "PUT"]


async def test_the_presets_then_the_owners(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    state["equaliser"] = equaliser()
    await setup(hass, aioclient_mock, entry, state)
    s = hass.states.get(ENTITY)
    assert s.state == "Rock"
    assert s.attributes["options"] == ["Flat", "Rock", "Evening"]
    assert s.attributes["presets"] == ["Flat", "Rock"]
    assert s.attributes["own"] == ["Evening"]


async def test_choosing_one_sends_its_key(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    state["equaliser"] = equaliser()
    await setup(hass, aioclient_mock, entry, state)
    aioclient_mock.put(f"{BASE}/equaliser", json={})
    await hass.services.async_call("select", "select_option", {ATTR_ENTITY_ID: ENTITY, "option": "Evening"}, blocking=True)
    assert puts(aioclient_mock) == [(f"{BASE}/equaliser", {"sel": "u1"})]


async def test_custom_is_shown_while_in_use_and_never_chosen(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    state["equaliser"] = equaliser(sel="custom")
    await setup(hass, aioclient_mock, entry, state)
    s = hass.states.get(ENTITY)
    assert s.state == "Custom"
    assert s.attributes["options"][0] == "Custom"
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call("select", "select_option", {ATTR_ENTITY_ID: ENTITY, "option": "Custom"}, blocking=True)
    assert puts(aioclient_mock) == []


async def test_no_equaliser_on_the_output_leaves_it_out(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    assert hass.states.get(ENTITY).state == STATE_UNAVAILABLE
