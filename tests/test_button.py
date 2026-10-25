"""Home, Now playing and Lyrics."""

from __future__ import annotations

from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

from .conftest import BASE, STATUS
from .test_media_player import setup

BUTTONS = {"home": "button.living_room_home", "now": "button.living_room_now_playing", "lyrics": "button.living_room_lyrics"}


async def test_each_button_sends_the_panel_there(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    for key, entity in BUTTONS.items():
        aioclient_mock.post(f"{BASE}/panel/go/{key}", json={})
        await hass.services.async_call("button", "press", {ATTR_ENTITY_ID: entity}, blocking=True)
    posts = [str(url) for method, url, _, _ in aioclient_mock.mock_calls if method == "POST"]
    assert posts == [f"{BASE}/panel/go/home", f"{BASE}/panel/go/now", f"{BASE}/panel/go/lyrics"]


async def test_with_nothing_active_only_home_is_there(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    state["active"] = None
    await setup(hass, aioclient_mock, entry, state)
    assert hass.states.get(BUTTONS["home"]).state != STATE_UNAVAILABLE
    assert hass.states.get(BUTTONS["now"]).state == STATE_UNAVAILABLE
    assert hass.states.get(BUTTONS["lyrics"]).state == STATE_UNAVAILABLE


async def test_a_player_without_a_screen_has_no_working_buttons(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    aioclient_mock.get(f"{BASE}/player/status", json={**STATUS, "screen": False})
    aioclient_mock.get(f"{BASE}/panel/dashboard", json={"shown": False, "by": None, "url": None})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await entry.runtime_data._on_state(state)
    await hass.async_block_till_done()
    for entity in BUTTONS.values():
        assert hass.states.get(entity).state == STATE_UNAVAILABLE
