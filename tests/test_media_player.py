"""The player as a media player."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import ATTR_INPUT_SOURCE, ATTR_MEDIA_VOLUME_LEVEL, MediaPlayerEntityFeature
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

from .conftest import BASE, STATUS

ENTITY = "media_player.living_room"


async def setup(hass: HomeAssistant, aioclient_mock, entry, state: dict[str, Any], dashboard_url=None):
    aioclient_mock.get(f"{BASE}/player/status", json=STATUS)
    aioclient_mock.get(f"{BASE}/panel/dashboard", json={"shown": False, "by": None, "url": dashboard_url})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    player = entry.runtime_data
    await player._on_state(state)
    await hass.async_block_till_done()
    return player


async def test_what_plays_and_what_can_be_done(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    s = hass.states.get(ENTITY)
    assert s.state == "playing"
    assert s.attributes["media_title"] == "Gymnopédie No. 1"
    assert s.attributes["media_artist"] == "Erik Satie"
    assert s.attributes["media_duration"] == 200.0
    assert s.attributes["media_position"] == 30.0
    assert s.attributes[ATTR_MEDIA_VOLUME_LEVEL] == 0.4
    assert s.attributes[ATTR_INPUT_SOURCE] == "Lyrion"
    assert "source_list" not in s.attributes, "a source is taken over from its own app"
    assert s.attributes["shuffle"] is False and s.attributes["repeat"] == "all"
    features = MediaPlayerEntityFeature(s.attributes["supported_features"])
    assert MediaPlayerEntityFeature.PAUSE in features and MediaPlayerEntityFeature.PLAY in features
    assert MediaPlayerEntityFeature.VOLUME_SET in features and MediaPlayerEntityFeature.SELECT_SOURCE not in features
    assert s.attributes["available_controls"] == ["next", "pause", "previous", "repeat", "shuffle"]


async def test_a_control_the_source_has_stays_while_it_cannot_work(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    """As the player shows it (ADR-0037 §3): Next at the end of the queue."""
    state["controls"]["available"] = ["pause", "previous", "repeat", "shuffle"]
    await setup(hass, aioclient_mock, entry, state)
    s = hass.states.get(ENTITY)
    assert MediaPlayerEntityFeature.NEXT_TRACK in MediaPlayerEntityFeature(s.attributes["supported_features"])
    assert "next" not in s.attributes["available_controls"]


async def test_a_source_without_shuffle_has_none(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    state["active"] = "spotify"
    state["controls"]["available"] = ["next", "pause", "previous"]
    await setup(hass, aioclient_mock, entry, state)
    features = MediaPlayerEntityFeature(hass.states.get(ENTITY).attributes["supported_features"])
    assert MediaPlayerEntityFeature.NEXT_TRACK in features
    assert MediaPlayerEntityFeature.SHUFFLE_SET not in features and MediaPlayerEntityFeature.REPEAT_SET not in features


async def test_nothing_playing_offers_no_transport(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    state["active"] = None
    state["controls"]["available"] = []
    await setup(hass, aioclient_mock, entry, state)
    features = MediaPlayerEntityFeature(hass.states.get(ENTITY).attributes["supported_features"])
    assert MediaPlayerEntityFeature.PLAY not in features and MediaPlayerEntityFeature.NEXT_TRACK not in features


async def test_artwork_on_the_players_own_lyrion_is_fetched_from_the_player(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    player = await setup(hass, aioclient_mock, entry, state)
    assert player.artwork(state["metadata"]["artwork"]) == "http://192.0.2.10:9000/music/1/cover_500x500_o.jpg"
    assert player.artwork("/plugins/x/mark") == f"{BASE}/plugins/x/mark"
    assert player.artwork("https://i.example/cover.jpg") == "https://i.example/cover.jpg"


async def test_a_track_playing_on_does_not_move_the_position_stamp(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    player = await setup(hass, aioclient_mock, entry, state)
    first = hass.states.get(ENTITY).attributes["media_position_updated_at"]
    state["metadata"]["position"] = 30.5
    await player._on_state(state)
    assert hass.states.get(ENTITY).attributes["media_position_updated_at"] == first
    state["metadata"]["position"] = 120.0
    await player._on_state(state)
    assert hass.states.get(ENTITY).attributes["media_position"] == 120.0, "a seek moves it"


async def test_commands_go_to_the_player(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    for path in ("/transport/pause", "/volume", "/transport/shuffle"):
        aioclient_mock.post(f"{BASE}{path}", json={})
    await hass.services.async_call("media_player", "media_pause", {ATTR_ENTITY_ID: ENTITY}, blocking=True)
    await hass.services.async_call(
        "media_player", "volume_set", {ATTR_ENTITY_ID: ENTITY, ATTR_MEDIA_VOLUME_LEVEL: 0.55}, blocking=True
    )
    await hass.services.async_call("media_player", "shuffle_set", {ATTR_ENTITY_ID: ENTITY, "shuffle": True}, blocking=True)
    posts = [(str(url), body) for method, url, body, _ in aioclient_mock.mock_calls if method == "POST"]
    assert posts == [
        (f"{BASE}/transport/pause", None),
        (f"{BASE}/volume", {"percent": 55}),
        (f"{BASE}/transport/shuffle", {"on": True}),
    ]


async def test_a_fixed_output_offers_no_volume(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    state["fixed_output"] = True
    await setup(hass, aioclient_mock, entry, state)
    s = hass.states.get(ENTITY)
    assert "volume_level" not in s.attributes
    assert MediaPlayerEntityFeature.VOLUME_SET not in MediaPlayerEntityFeature(s.attributes["supported_features"])


async def test_a_fixed_output_with_a_control_mutes(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    """ADR-0165: mute with Fixed volume where the output has a control."""
    state["fixed_output"] = True
    state["fixed_mute"] = False
    player = await setup(hass, aioclient_mock, entry, state)
    s = hass.states.get(ENTITY)
    features = MediaPlayerEntityFeature(s.attributes["supported_features"])
    assert MediaPlayerEntityFeature.VOLUME_MUTE in features
    assert MediaPlayerEntityFeature.VOLUME_SET not in features
    assert s.attributes["is_volume_muted"] is False
    aioclient_mock.post(f"{BASE}/volume/mute", json={})
    await hass.services.async_call(
        "media_player", "volume_mute", {ATTR_ENTITY_ID: ENTITY, "is_volume_muted": True}, blocking=True
    )
    posts = [(str(url), body) for method, url, body, _ in aioclient_mock.mock_calls if method == "POST"]
    assert posts == [(f"{BASE}/volume/mute", {"muted": True})]
    state["fixed_mute"] = True
    await player._on_state(state)
    assert hass.states.get(ENTITY).attributes["is_volume_muted"] is True


async def test_a_fixed_output_without_a_control_has_no_mute(
    hass: HomeAssistant, aioclient_mock, entry, state, no_socket
) -> None:
    state["fixed_output"] = True
    state["fixed_mute"] = None
    await setup(hass, aioclient_mock, entry, state)
    features = MediaPlayerEntityFeature(hass.states.get(ENTITY).attributes["supported_features"])
    assert MediaPlayerEntityFeature.VOLUME_MUTE not in features


async def test_a_source_that_seeks_is_sought(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    """ADR-0164 C2: seeking where the source declares it."""
    state["capabilities"]["lms"]["controls"].append("seek")
    await setup(hass, aioclient_mock, entry, state)
    features = MediaPlayerEntityFeature(hass.states.get(ENTITY).attributes["supported_features"])
    assert MediaPlayerEntityFeature.SEEK in features
    aioclient_mock.post(f"{BASE}/transport/seek", json={})
    await hass.services.async_call("media_player", "media_seek", {ATTR_ENTITY_ID: ENTITY, "seek_position": 95.5}, blocking=True)
    posts = [(str(url), body) for method, url, body, _ in aioclient_mock.mock_calls if method == "POST"]
    assert posts == [(f"{BASE}/transport/seek", {"position": 95.5})]


async def test_a_source_that_does_not_seek_is_not(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    features = MediaPlayerEntityFeature(hass.states.get(ENTITY).attributes["supported_features"])
    assert MediaPlayerEntityFeature.SEEK not in features


async def test_nothing_active_is_idle(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    state["active"] = None
    state["metadata"] = {}
    state["controls"] = None
    await setup(hass, aioclient_mock, entry, state)
    assert hass.states.get(ENTITY).state == "idle"


async def test_a_lost_connection_makes_it_unavailable(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    player = await setup(hass, aioclient_mock, entry, state)
    player.state = None
    player._notify()
    assert hass.states.get(ENTITY).state == STATE_UNAVAILABLE
