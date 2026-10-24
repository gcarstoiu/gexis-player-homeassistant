"""The screen, the dashboard and the visualiser."""

from __future__ import annotations

from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

from .conftest import BASE, STATUS
from .test_media_player import setup


async def test_the_screen_follows_standby_and_sets_it(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    player = await setup(hass, aioclient_mock, entry, state)
    assert hass.states.get("switch.living_room_screen").state == STATE_ON
    aioclient_mock.post(f"{BASE}/panel/standby/on", json={"standby": True})
    await hass.services.async_call("switch", "turn_off", {ATTR_ENTITY_ID: "switch.living_room_screen"}, blocking=True)
    assert any(str(url) == f"{BASE}/panel/standby/on" for _, url, _, _ in aioclient_mock.mock_calls)
    state["panel"]["standby"] = True
    await player._on_state(state)
    assert hass.states.get("switch.living_room_screen").state == STATE_OFF


async def test_the_dashboard_needs_an_address(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    assert hass.states.get("switch.living_room_dashboard").state == STATE_UNAVAILABLE
    assert hass.states.get("switch.living_room_visualiser").state == STATE_OFF


async def test_the_dashboard_with_an_address(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state, dashboard_url="http://ha.example:8123/room/home")
    assert hass.states.get("switch.living_room_dashboard").state == STATE_OFF
    aioclient_mock.post(f"{BASE}/panel/dashboard/show", json={})
    await hass.services.async_call("switch", "turn_on", {ATTR_ENTITY_ID: "switch.living_room_dashboard"}, blocking=True)
    assert any(str(url) == f"{BASE}/panel/dashboard/show" for _, url, _, _ in aioclient_mock.mock_calls)


async def test_a_player_without_a_screen_has_no_working_switches(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    aioclient_mock.get(f"{BASE}/player/status", json={**STATUS, "screen": False})
    aioclient_mock.get(f"{BASE}/panel/dashboard", json={"shown": False, "by": None, "url": None})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await entry.runtime_data._on_state(state)
    await hass.async_block_till_done()
    for key in ("screen", "dashboard", "visualiser"):
        assert hass.states.get(f"switch.living_room_{key}").state == STATE_UNAVAILABLE
