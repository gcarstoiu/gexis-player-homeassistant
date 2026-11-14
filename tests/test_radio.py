"""Internet radio in Home Assistant (Gexis Player's ADR-0180 item 10): the
player's favourites as the media player's sources, its station directory in
the media browser and its search, and the heart."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from homeassistant.components.media_player import ATTR_INPUT_SOURCE, MediaPlayerEntityFeature
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.gexis.media_player import station_id, station_of

from .conftest import BASE
from .test_media_player import ENTITY, setup

FAVOURITES = [
    {"id": "f-1", "name": "Ostkreuz FM", "url": "https://stream.example.org/1", "logo": "/stations/logo/aaaaaaaaaaaaaaaa",
     "country": "Germany", "codec": "AAC", "bitrate": 128, "hls": False, "listed": True},
    {"id": "address-2", "name": "Kiez Jazz Nacht", "url": "https://stream.example.org/2", "logo": None,
     "country": None, "codec": "MP3", "bitrate": 128, "hls": False, "listed": False},
]
LISTED = {"id": "s-9", "name": "Elbe Welle", "url": "https://stream.example.org/9", "logo": "/stations/logo/bbbbbbbbbbbbbbbb",
          "country": "Germany", "countrycode": "DE", "codec": "AAC", "bitrate": 48, "hls": False, "listed": True,
          "favourite": False}


def radio_state(state: dict[str, Any], *, playing: dict[str, Any] | None = FAVOURITES[0], favourite=True, revision=1):
    state = copy.deepcopy(state)
    state["available"] = {"lms": True, "spotify": True, "bluetooth": True, "radio": True}
    state["sources"].append({"id": "radio", "name": "Internet radio"})
    state["capabilities"]["radio"] = {"controls": ["next", "pause", "play", "previous"]}
    state["radio"] = {"station": {**playing, "favourite": favourite} if playing else None, "state": "playing",
                      "attempt": 0, "tries": 3, "lines": "split", "favourites": revision}
    if playing:
        state["active"] = "radio"
        state["metadata"] = {"title": "Clair de lune", "artist": "Claude Debussy", "album": playing["name"],
                             "artwork": playing.get("logo"), "transport": "playing", "source_type": "radio"}
        state["controls"] = {"available": ["next", "pause", "previous"] if favourite else ["pause"]}
    return state


@pytest.fixture
def favourites_route(aioclient_mock):
    aioclient_mock.get(f"{BASE}/stations/favourites", json={"favourites": FAVOURITES})


async def test_the_favourites_are_the_sources(hass: HomeAssistant, aioclient_mock, entry, state, no_socket,
                                              favourites_route) -> None:
    await setup(hass, aioclient_mock, entry, radio_state(state))
    s = hass.states.get(ENTITY)
    assert s.attributes["source_list"] == ["Ostkreuz FM", "Kiez Jazz Nacht"]
    assert s.attributes[ATTR_INPUT_SOURCE] == "Ostkreuz FM", "a favourite playing is its own source"
    features = MediaPlayerEntityFeature(s.attributes["supported_features"])
    for feature in (MediaPlayerEntityFeature.SELECT_SOURCE, MediaPlayerEntityFeature.BROWSE_MEDIA,
                    MediaPlayerEntityFeature.PLAY_MEDIA, MediaPlayerEntityFeature.SEARCH_MEDIA):
        assert feature in features
    assert s.attributes["radio"] == {"station": "f-1", "favourite": True, "state": "playing"}

    aioclient_mock.post(f"{BASE}/stations/play", json={"ok": True})
    await hass.services.async_call("media_player", "select_source",
                                   {ATTR_ENTITY_ID: ENTITY, ATTR_INPUT_SOURCE: "Kiez Jazz Nacht"}, blocking=True)
    posts = [(str(url), body) for method, url, body, _ in aioclient_mock.mock_calls if method == "POST"]
    assert posts == [(f"{BASE}/stations/play", {"favourite": "address-2"})]
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("media_player", "select_source",
                                       {ATTR_ENTITY_ID: ENTITY, ATTR_INPUT_SOURCE: "Lyrion"}, blocking=True)


async def test_another_station_shows_the_radio_as_the_source(hass: HomeAssistant, aioclient_mock, entry, state,
                                                             no_socket, favourites_route) -> None:
    await setup(hass, aioclient_mock, entry, radio_state(state, playing=LISTED, favourite=False))
    assert hass.states.get(ENTITY).attributes[ATTR_INPUT_SOURCE] == "Internet radio"


async def test_the_favourites_are_read_again_when_they_change(hass: HomeAssistant, aioclient_mock, entry, state,
                                                              no_socket, favourites_route) -> None:
    player = await setup(hass, aioclient_mock, entry, radio_state(state))
    reads = lambda: sum(1 for m, u, *_ in aioclient_mock.mock_calls if m == "GET" and str(u).endswith("/stations/favourites"))  # noqa: E731
    assert reads() == 1
    await player._on_state(radio_state(state))
    assert reads() == 1, "the same revision is not read again"
    await player._on_state(radio_state(state, revision=2))
    assert reads() == 2


async def test_without_the_radio_nothing_of_it_is_offered(hass: HomeAssistant, aioclient_mock, entry, state,
                                                          no_socket, favourites_route) -> None:
    off = radio_state(state, playing=None)
    off["available"]["radio"] = False
    await setup(hass, aioclient_mock, entry, off)
    s = hass.states.get(ENTITY)
    assert "source_list" not in s.attributes and "radio" not in s.attributes
    features = MediaPlayerEntityFeature(s.attributes["supported_features"])
    assert MediaPlayerEntityFeature.BROWSE_MEDIA not in features
    assert MediaPlayerEntityFeature.SELECT_SOURCE not in features


async def test_an_older_player_is_as_before(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state)
    s = hass.states.get(ENTITY)
    assert "source_list" not in s.attributes
    assert MediaPlayerEntityFeature.BROWSE_MEDIA not in MediaPlayerEntityFeature(s.attributes["supported_features"])
    assert not any(str(u).endswith("/stations/favourites") for _, u, *_ in aioclient_mock.mock_calls)


async def browse(hass_ws_client, hass, content_id=None):
    client = await hass_ws_client(hass)
    message = {"id": 5, "type": "media_player/browse_media", "entity_id": ENTITY}
    if content_id:
        message.update(media_content_type="gexis_radio", media_content_id=content_id)
    await client.send_json(message)
    return await client.receive_json()


async def test_the_directory_in_the_media_browser(hass: HomeAssistant, aioclient_mock, entry, state, no_socket,
                                                  favourites_route, hass_ws_client) -> None:
    await setup(hass, aioclient_mock, entry, radio_state(state))
    root = (await browse(hass_ws_client, hass))["result"]
    assert root["title"] == "Internet radio"
    assert [c["title"] for c in root["children"]] == ["Favourites", "Popular here", "By genre", "By country",
                                                     "By language"]

    favourites = (await browse(hass_ws_client, hass, "gexis:radio/favourites"))["result"]["children"]
    assert [c["title"] for c in favourites] == ["Ostkreuz FM", "Kiez Jazz Nacht"]
    assert favourites[0]["media_content_id"] == "gexis:favourite/f-1" and favourites[0]["can_play"]
    assert "/api/media_player_proxy/" in favourites[0]["thumbnail"], "logos through Home Assistant's proxy"
    assert favourites[1]["thumbnail"] is None

    aioclient_mock.get(f"{BASE}/stations/popular", json={"stations": [LISTED], "offset": 0, "end": True})
    popular = (await browse(hass_ws_client, hass, "gexis:radio/popular"))["result"]["children"]
    assert [c["title"] for c in popular] == ["Elbe Welle"]
    assert station_of(popular[0]["media_content_id"])["url"] == LISTED["url"]

    aioclient_mock.get(f"{BASE}/stations/genres", json={"genres": [{"name": "jazz", "stations": 1240}]})
    genres = (await browse(hass_ws_client, hass, "gexis:radio/genres"))["result"]["children"]
    assert [(c["title"], c["media_content_id"]) for c in genres] == [("jazz", "gexis:radio/genre/jazz")]
    aioclient_mock.get(f"{BASE}/stations/list", json={"stations": [LISTED], "offset": 0, "end": True})
    jazz = (await browse(hass_ws_client, hass, "gexis:radio/genre/jazz"))["result"]
    assert jazz["children"][0]["title"] == "Elbe Welle"
    asked = [u for m, u, *_ in aioclient_mock.mock_calls if m == "GET" and "/stations/list" in str(u)]
    assert asked and asked[-1].query["genre"] == "jazz"

    aioclient_mock.get(f"{BASE}/stations/countries", json={"countries": [{"code": "DE", "name": "Germany", "stations": 5592}]})
    countries = (await browse(hass_ws_client, hass, "gexis:radio/countries"))["result"]["children"]
    assert countries[0]["media_content_id"] == "gexis:radio/country/DE"


async def test_the_directory_down_is_said(hass: HomeAssistant, aioclient_mock, entry, state, no_socket,
                                          favourites_route, hass_ws_client) -> None:
    await setup(hass, aioclient_mock, entry, radio_state(state))
    aioclient_mock.get(f"{BASE}/stations/popular", status=503, json={"error": "x", "reachable": False})
    answer = await browse(hass_ws_client, hass, "gexis:radio/popular")
    assert not answer["success"] and "cannot be reached" in answer["error"]["message"]


async def test_a_station_from_the_browser_plays(hass: HomeAssistant, aioclient_mock, entry, state, no_socket,
                                                favourites_route) -> None:
    await setup(hass, aioclient_mock, entry, radio_state(state))
    aioclient_mock.post(f"{BASE}/stations/play", json={"ok": True})
    for content_id in (station_id(LISTED), "gexis:favourite/f-1"):
        await hass.services.async_call("media_player", "play_media", {
            ATTR_ENTITY_ID: ENTITY, "media_content_type": "channel", "media_content_id": content_id}, blocking=True)
    posts = [body for method, url, body, _ in aioclient_mock.mock_calls if method == "POST"]
    sent = {k: v for k, v in LISTED.items() if k != "favourite"}
    assert posts == [{"station": sent}, {"favourite": "f-1"}]
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("media_player", "play_media", {
            ATTR_ENTITY_ID: ENTITY, "media_content_type": "channel", "media_content_id": "nonsense"}, blocking=True)


async def test_search_by_name(hass: HomeAssistant, aioclient_mock, entry, state, no_socket, favourites_route,
                              hass_ws_client) -> None:
    await setup(hass, aioclient_mock, entry, radio_state(state))
    aioclient_mock.get(f"{BASE}/stations/search", json={"stations": [LISTED], "offset": 0, "end": True})
    client = await hass_ws_client(hass)
    await client.send_json({"id": 7, "type": "media_player/search_media", "entity_id": ENTITY,
                            "search_query": "elbe"})
    answer = await client.receive_json()
    assert answer["success"], answer
    assert [r["title"] for r in answer["result"]["result"]] == ["Elbe Welle"]
    asked = [u for m, u, *_ in aioclient_mock.mock_calls if m == "GET" and "/stations/search" in str(u)]
    assert asked[-1].query["q"] == "elbe"


async def test_the_heart_on_the_station_playing(hass: HomeAssistant, aioclient_mock, entry, state, no_socket,
                                                favourites_route) -> None:
    await setup(hass, aioclient_mock, entry, radio_state(state, playing=LISTED, favourite=False))
    aioclient_mock.post(f"{BASE}/stations/favourites", json={"added": True})
    aioclient_mock.delete(f"{BASE}/stations/favourites/s-9", json={"ok": True})
    await hass.services.async_call("gexis", "radio_favourite", {ATTR_ENTITY_ID: ENTITY, "favourite": True}, blocking=True)
    await hass.services.async_call("gexis", "radio_favourite", {ATTR_ENTITY_ID: ENTITY, "favourite": False}, blocking=True)
    calls = [(m, str(u), b) for m, u, b, _ in aioclient_mock.mock_calls if m in ("POST", "DELETE")]
    assert calls[0][0] == "POST" and calls[0][2]["station"]["id"] == "s-9"
    assert calls[1][:2] == ("DELETE", f"{BASE}/stations/favourites/s-9")


async def test_the_heart_with_nothing_playing_is_refused(hass: HomeAssistant, aioclient_mock, entry, state,
                                                         no_socket, favourites_route) -> None:
    await setup(hass, aioclient_mock, entry, radio_state(state, playing=None))
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("gexis", "radio_favourite", {ATTR_ENTITY_ID: ENTITY, "favourite": True},
                                       blocking=True)


async def test_a_stopped_station_shows_as_paused_and_play_starts_it(hass: HomeAssistant, aioclient_mock, entry,
                                                                   state, no_socket, favourites_route) -> None:
    """A station stops rather than pauses, and the player keeps it: shown as
    paused, with Play, rather than as nothing playing (George, 2026-11-14)."""
    stopped = radio_state(state)
    stopped["metadata"]["transport"] = "stopped"
    stopped["radio"]["state"] = "stopped"
    stopped["controls"] = {"available": ["next", "pause", "play", "previous"]}
    await setup(hass, aioclient_mock, entry, stopped)
    s = hass.states.get(ENTITY)
    assert s.state == "paused"
    assert MediaPlayerEntityFeature.PLAY in MediaPlayerEntityFeature(s.attributes["supported_features"])
    aioclient_mock.post(f"{BASE}/transport/play", json={})
    await hass.services.async_call("media_player", "media_play", {ATTR_ENTITY_ID: ENTITY}, blocking=True)
    posts = [str(url) for method, url, *_ in aioclient_mock.mock_calls if method == "POST"]
    assert posts == [f"{BASE}/transport/play"]


async def test_another_source_stopped_is_still_idle(hass: HomeAssistant, aioclient_mock, entry, state,
                                                    no_socket) -> None:
    stopped = copy.deepcopy(state)
    stopped["metadata"]["transport"] = "stopped"
    await setup(hass, aioclient_mock, entry, stopped)
    assert stopped["active"] and stopped["active"] != "radio"
    assert hass.states.get(ENTITY).state == "idle"


def test_a_station_carries_itself_through_its_id() -> None:
    assert station_of(station_id(LISTED)) == {k: v for k, v in LISTED.items() if k != "favourite"}
    assert station_of("gexis:station/!!!") is None


async def test_the_cards_radio_view_has_the_favourites_with_their_lines(
        hass: HomeAssistant, aioclient_mock, entry, state, no_socket, favourites_route, hass_ws_client) -> None:
    await setup(hass, aioclient_mock, entry, radio_state(state))
    client = await hass_ws_client(hass)
    await client.send_json({"id": 9, "type": "gexis/radio", "entity_id": ENTITY})
    answer = await client.receive_json()
    assert answer["success"], answer
    result = answer["result"]
    assert result["playing"] == "f-1" and result["state"] == "playing" and result["enabled"] is True
    first, second = result["favourites"]
    assert (first["name"], first["meta"], first["content_id"]) == ("Ostkreuz FM", "Germany · AAC · 128 kb/s",
                                                                   "gexis:favourite/f-1")
    assert "/api/media_player_proxy/" in first["thumbnail"] and second["thumbnail"] is None
    assert second["meta"] == "MP3 · 128 kb/s"
    await client.send_json({"id": 10, "type": "gexis/radio", "entity_id": "media_player.nothing"})
    assert not (await client.receive_json())["success"]
