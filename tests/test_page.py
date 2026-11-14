"""A page of Home Assistant's on the player's screen, for a while (ADR-0176)."""

from __future__ import annotations

import json

import pytest

from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .conftest import BASE, STATUS
from .test_media_player import ENTITY, setup

SENSOR = "binary_sensor.living_room_page"
URL = "http://ha.example:8123/home-security/tv"


def _sent(aioclient_mock, path):
    return [data for _, url, data, _ in aioclient_mock.mock_calls if str(url) == f"{BASE}{path}"]


async def test_show_and_hide_reach_the_player(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    state["panel"]["pages"] = True
    await setup(hass, aioclient_mock, entry, state)
    aioclient_mock.post(f"{BASE}/panel/page/show", json={"shown": True})
    aioclient_mock.post(f"{BASE}/panel/page/hide", json={"hidden": True})
    await hass.services.async_call(
        "gexis", "show_page", {ATTR_ENTITY_ID: ENTITY, "url": URL, "id": "cameras", "seconds": 120}, blocking=True
    )
    await hass.services.async_call("gexis", "hide_page", {ATTR_ENTITY_ID: ENTITY, "id": "cameras"}, blocking=True)
    await hass.services.async_call("gexis", "hide_page", {ATTR_ENTITY_ID: ENTITY}, blocking=True)
    assert _sent(aioclient_mock, "/panel/page/show") == [{"url": URL, "id": "cameras", "seconds": 120}]
    assert _sent(aioclient_mock, "/panel/page/hide") == [{"id": "cameras"}, None]


async def test_the_players_refusal_is_the_actions_error(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    await setup(hass, aioclient_mock, entry, state)
    aioclient_mock.post(
        f"{BASE}/panel/page/show", status=403,
        json={"error": "Pages from Home Assistant are off on this player: switch them on in Settings → Display."},
    )
    with pytest.raises(HomeAssistantError, match="Pages from Home Assistant are off"):
        await hass.services.async_call("gexis", "show_page", {ATTR_ENTITY_ID: ENTITY, "url": URL}, blocking=True)


async def test_an_older_player_is_asked_to_update(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    aioclient_mock.post(f"{BASE}/panel/page/show", status=404, json={"error": "Not Found"})
    with pytest.raises(HomeAssistantError, match="too old to show a page"):
        await hass.services.async_call("gexis", "show_page", {ATTR_ENTITY_ID: ENTITY, "url": URL}, blocking=True)


@pytest.mark.parametrize("data", [
    {"url": "ftp://ha.example/x"},
    {"url": URL, "seconds": 5},
    {"url": URL, "seconds": 3601},
    {"url": URL, "id": ""},
    {},
])
async def test_a_call_out_of_bounds_never_reaches_the_player(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket, data
) -> None:
    await setup(hass, aioclient_mock, entry, state)
    with pytest.raises(Exception):
        await hass.services.async_call("gexis", "show_page", {ATTR_ENTITY_ID: ENTITY, **data}, blocking=True)
    assert _sent(aioclient_mock, "/panel/page/show") == []


async def test_the_page_sensor_follows_the_panel(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    state["panel"]["pages"] = True
    state["panel"]["page"] = {"shown": False, "id": None, "until": None, "seq": 0, "closed": None}
    player = await setup(hass, aioclient_mock, entry, state)
    assert hass.states.get(SENSOR).state == STATE_OFF
    state["panel"]["page"] = {"shown": True, "id": "cameras", "until": 1762530000.0, "seq": 1, "closed": None}
    await player._on_state(state)
    s = hass.states.get(SENSOR)
    assert s.state == STATE_ON and s.attributes["page_id"] == "cameras"
    state["panel"]["page"] = {"shown": False, "id": None, "until": None, "seq": 1,
                              "closed": {"id": "cameras", "by": "touch", "at": 1762529900.0}}
    await player._on_state(state)
    s = hass.states.get(SENSOR)
    assert s.state == STATE_OFF and s.attributes["closed_by"] == "touch" and s.attributes["closed_id"] == "cameras"


async def test_the_page_sensor_is_unavailable_while_the_player_allows_none(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    state["panel"]["pages"] = False
    player = await setup(hass, aioclient_mock, entry, state)
    assert hass.states.get(SENSOR).state == STATE_UNAVAILABLE
    state["panel"]["pages"] = True
    await player._on_state(state)
    assert hass.states.get(SENSOR).state == STATE_OFF


async def test_an_older_player_says_nothing_of_pages_and_gets_none(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    await setup(hass, aioclient_mock, entry, state)
    assert hass.states.get(SENSOR).state == STATE_UNAVAILABLE


async def test_a_player_without_a_screen_has_no_page(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    state["panel"]["pages"] = True
    aioclient_mock.get(f"{BASE}/player/status", json={**STATUS, "screen": False})
    aioclient_mock.get(f"{BASE}/panel/dashboard", json={"shown": False, "by": None, "url": None})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await entry.runtime_data._on_state(state)
    await hass.async_block_till_done()
    assert hass.states.get(SENSOR).state == STATE_UNAVAILABLE


def test_every_action_and_field_is_described() -> None:
    from pathlib import Path

    import yaml

    root = Path(__file__).parents[1] / "custom_components" / "gexis"
    services = yaml.safe_load((root / "services.yaml").read_text())
    text = json.loads((root / "translations" / "en.json").read_text())["services"]
    icons = json.loads((root / "icons.json").read_text())["services"]
    assert set(services) == set(text) == set(icons) == {"show_page", "hide_page", "preload_page", "radio_favourite"}
    for name, spec in services.items():
        assert set(spec["fields"]) == set(text[name]["fields"]), name


# --- one page kept loaded (ADR-0176's amendment) ----------------------------

async def test_the_page_to_keep_reaches_the_player_and_empty_clears_it(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    state["panel"]["pages"] = True
    await setup(hass, aioclient_mock, entry, state)
    aioclient_mock.post(f"{BASE}/panel/page/preload", json={"preloaded": True})
    await hass.services.async_call("gexis", "preload_page", {ATTR_ENTITY_ID: ENTITY, "url": URL}, blocking=True)
    await hass.services.async_call("gexis", "preload_page", {ATTR_ENTITY_ID: ENTITY, "url": ""}, blocking=True)
    await hass.services.async_call("gexis", "preload_page", {ATTR_ENTITY_ID: ENTITY}, blocking=True)
    assert _sent(aioclient_mock, "/panel/page/preload") == [{"url": URL}, {"url": None}, {"url": None}]


async def test_a_page_to_keep_that_is_no_address_never_reaches_the_player(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    await setup(hass, aioclient_mock, entry, state)
    with pytest.raises(Exception):
        await hass.services.async_call(
            "gexis", "preload_page", {ATTR_ENTITY_ID: ENTITY, "url": "ftp://ha.example/x"}, blocking=True
        )
    assert _sent(aioclient_mock, "/panel/page/preload") == []


async def test_the_page_sensor_says_whether_a_page_is_kept_never_its_address(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    state["panel"]["pages"] = True
    state["panel"]["page"] = {"shown": False, "id": None, "until": None, "seq": 0, "closed": None,
                              "preloaded": False}
    player = await setup(hass, aioclient_mock, entry, state)
    assert hass.states.get(SENSOR).attributes["preloaded"] is False
    state["panel"]["page"] = {**state["panel"]["page"], "seq": 1, "preloaded": True}
    await player._on_state(state)
    s = hass.states.get(SENSOR)
    assert s.attributes["preloaded"] is True and URL not in repr(s.attributes)
