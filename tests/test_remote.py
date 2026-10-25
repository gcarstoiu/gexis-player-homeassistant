"""The D-pad, as a remote (ADR-0161 D7)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .conftest import BASE, STATUS
from .test_media_player import setup

REMOTE = "remote.living_room_d_pad"


def posts(aioclient_mock) -> list[tuple[str, object]]:
    return [(str(url), data) for method, url, data, _ in aioclient_mock.mock_calls if method == "POST"]


async def send(hass: HomeAssistant, command, **extra) -> None:
    await hass.services.async_call(
        "remote", "send_command", {ATTR_ENTITY_ID: REMOTE, "command": command, **extra}, blocking=True
    )


async def test_each_key_is_sent_and_home_goes_home(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    aioclient_mock.post(f"{BASE}/panel/key", json={"key": "x"})
    aioclient_mock.post(f"{BASE}/panel/go/home", json={})
    await send(hass, ["up", "down", "left", "right", "ok", "back", "home"], delay_secs=0)
    assert posts(aioclient_mock) == [
        *[(f"{BASE}/panel/key", {"key": k}) for k in ("up", "down", "left", "right", "ok", "back")],
        (f"{BASE}/panel/go/home", None),
    ]


async def test_repeats_with_the_delay_between(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    aioclient_mock.post(f"{BASE}/panel/key", json={"key": "down"})
    with patch("custom_components.gexis.remote.asyncio.sleep", new=AsyncMock()) as sleep:
        await send(hass, "down", num_repeats=3, delay_secs=0.25)
    assert posts(aioclient_mock) == [(f"{BASE}/panel/key", {"key": "down"})] * 3
    assert [c.args[0] for c in sleep.await_args_list] == [0.25, 0.25], "a delay between presses, none before the first"


async def test_an_unknown_command_is_refused_before_anything_is_sent(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    await setup(hass, aioclient_mock, entry, state)
    with pytest.raises(ServiceValidationError, match="volume_up"):
        await send(hass, ["up", "volume_up"])
    assert posts(aioclient_mock) == []


async def test_a_player_released_before_the_d_pad_asks_to_be_updated(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    await setup(hass, aioclient_mock, entry, state)
    aioclient_mock.post(f"{BASE}/panel/key", status=404, text="404: Not Found")
    with pytest.raises(HomeAssistantError, match="too old for the D-pad. Update it first"):
        await send(hass, "up")


async def test_the_players_refusal_is_said(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    aioclient_mock.post(f"{BASE}/panel/key", status=409, json={"error": "this player has no screen"})
    with pytest.raises(HomeAssistantError, match="Living Room: this player has no screen"):
        await send(hass, "ok")


async def test_on_follows_the_screen_and_turns_it(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    player = await setup(hass, aioclient_mock, entry, state)
    assert hass.states.get(REMOTE).state == STATE_ON
    state["panel"]["standby"] = True
    await player._on_state(state)
    await hass.async_block_till_done()
    assert hass.states.get(REMOTE).state == STATE_OFF
    aioclient_mock.post(f"{BASE}/panel/standby/off", json={})
    aioclient_mock.post(f"{BASE}/panel/standby/on", json={})
    await hass.services.async_call("remote", "turn_on", {ATTR_ENTITY_ID: REMOTE}, blocking=True)
    await hass.services.async_call("remote", "turn_off", {ATTR_ENTITY_ID: REMOTE}, blocking=True)
    assert [u for u, _ in posts(aioclient_mock)] == [f"{BASE}/panel/standby/off", f"{BASE}/panel/standby/on"]


async def test_a_player_without_a_screen_has_no_working_remote(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    aioclient_mock.get(f"{BASE}/player/status", json={**STATUS, "screen": False})
    aioclient_mock.get(f"{BASE}/panel/dashboard", json={"shown": False, "by": None, "url": None})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await entry.runtime_data._on_state(state)
    await hass.async_block_till_done()
    assert hass.states.get(REMOTE).state == STATE_UNAVAILABLE
