"""Home Assistant's own join and unjoin, on the player's groups (its ADR-0166)."""

from __future__ import annotations

import copy
from typing import Any

from homeassistant.components.media_player import ATTR_GROUP_MEMBERS, MediaPlayerEntityFeature
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.gexis.const import DOMAIN

from .conftest import BASE, STATUS

ENTITY = "media_player.living_room"
KITCHEN_ID = "9a1b2c3d4e5f6071"


async def setup(hass: HomeAssistant, aioclient_mock, entry, state: dict[str, Any], status: dict[str, Any]):
    aioclient_mock.get(f"{BASE}/player/status", json=status)
    aioclient_mock.get(f"{BASE}/panel/dashboard", json={"shown": False, "by": None, "url": None})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    player = entry.runtime_data
    await player._on_state(state)
    await hass.async_block_till_done()
    return player


def kitchen(hass: HomeAssistant) -> str:
    """Another Gexis player Home Assistant knows."""
    return er.async_get(hass).async_get_or_create(
        "media_player", DOMAIN, KITCHEN_ID, suggested_object_id="kitchen").entity_id


def group(leader: str, me: str) -> dict[str, Any]:
    ids = [STATUS["id"], KITCHEN_ID, "0000000000000000"]
    ordered = [leader] + [i for i in ids if i != leader]
    return {"id": "g1", "revision": 2, "leader": leader, "me": me, "mode": "snapcast", "silent": False,
            "members": [{"id": i, "name": i, "me": i == me, "leads": i == leader} for i in ordered]}


async def test_a_player_older_than_groups_offers_no_join(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    await setup(hass, aioclient_mock, entry, state, STATUS)
    features = MediaPlayerEntityFeature(hass.states.get(ENTITY).attributes["supported_features"])
    assert MediaPlayerEntityFeature.GROUPING not in features


async def test_the_group_is_its_members_the_leader_first(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    other = kitchen(hass)
    state["group"] = group(KITCHEN_ID, STATUS["id"])
    await setup(hass, aioclient_mock, entry, state, {**STATUS, "multiroom": 1})
    s = hass.states.get(ENTITY)
    assert MediaPlayerEntityFeature.GROUPING in MediaPlayerEntityFeature(s.attributes["supported_features"])
    # The third member is a player Home Assistant does not know: left out.
    assert s.attributes[ATTR_GROUP_MEMBERS] == [other, ENTITY]


async def test_join_joins_the_others_to_this_player(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    other = kitchen(hass)
    await setup(hass, aioclient_mock, entry, state, {**STATUS, "multiroom": 1})
    aioclient_mock.post(f"{BASE}/group/join", json={"record": None})
    await hass.services.async_call("media_player", "join", {ATTR_ENTITY_ID: ENTITY, ATTR_GROUP_MEMBERS: [other]},
                                   blocking=True)
    calls = [c for c in aioclient_mock.mock_calls if str(c[1]).endswith("/group/join")]
    assert calls and calls[0][2] == {"player": KITCHEN_ID}


async def test_unjoin_leaves_and_the_leader_undoes(hass: HomeAssistant, aioclient_mock, entry, state, no_socket) -> None:
    kitchen(hass)
    state["group"] = group(KITCHEN_ID, STATUS["id"])
    player = await setup(hass, aioclient_mock, entry, state, {**STATUS, "multiroom": 1})
    aioclient_mock.post(f"{BASE}/group/leave", json={"record": None})
    aioclient_mock.post(f"{BASE}/group/undo", json={"record": None})
    await hass.services.async_call("media_player", "unjoin", {ATTR_ENTITY_ID: ENTITY}, blocking=True)
    assert [str(c[1]).rsplit("/", 1)[-1] for c in aioclient_mock.mock_calls if "/group/" in str(c[1])] == ["leave"]
    leading = copy.deepcopy(state)
    leading["group"] = group(STATUS["id"], STATUS["id"])
    await player._on_state(leading)
    await hass.async_block_till_done()
    await hass.services.async_call("media_player", "unjoin", {ATTR_ENTITY_ID: ENTITY}, blocking=True)
    assert [str(c[1]).rsplit("/", 1)[-1] for c in aioclient_mock.mock_calls if "/group/" in str(c[1])] == ["leave", "undo"]
