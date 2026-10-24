"""Fixtures: a player's status and live state, as the player sends them."""

from __future__ import annotations

from collections.abc import Generator
import copy
from typing import Any
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gexis.const import DOMAIN

HOST = "192.0.2.10"
BASE = f"http://{HOST}:8090"
STATUS = {
    "name": "Living Room",
    "host": "livingroom.local",
    "instance": "0" * 32,
    "id": "3f2a9c41d07b5e86",
    "screen": True,
    "transport": "playing",
    "renderer": "Lyrion",
}
STATE: dict[str, Any] = {
    "active": "lms",
    "metadata": {
        "track_id": "1",
        "title": "Gymnopédie No. 1",
        "artist": "Erik Satie",
        "album": "Gymnopédies",
        "artwork": "http://127.0.0.1:9000/music/1/cover_500x500_o.jpg",
        "position": 30.0,
        "duration": 200.0,
        "transport": "playing",
    },
    "capabilities": {
        "lms": {"controls": ["activate", "next", "pause", "play", "previous", "repeat", "shuffle"]},
        "spotify": {"controls": ["activate", "next", "pause", "play", "previous"]},
        "bluetooth": {"controls": []},
    },
    "sources": [
        {"id": "lms", "name": "Lyrion"},
        {"id": "spotify", "name": "Spotify"},
        {"id": "bluetooth", "name": "Bluetooth"},
    ],
    "controls": {"available": ["next", "pause", "previous", "repeat", "shuffle"], "shuffle": False, "repeat": "all"},
    "volume": {"percent": 40, "raw": 0, "db": -27.0, "muted": False},
    "fixed_output": False,
    "settings_revision": 1,
    "panel": {"standby": False, "visualiser": False, "dashboard": {"shown": False, "by": None}},
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load custom_components/gexis."""


@pytest.fixture
def state() -> dict[str, Any]:
    return copy.deepcopy(STATE)


@pytest.fixture
def entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN, unique_id=STATUS["id"], title=STATUS["name"], data={"host": HOST, "port": 8090}
    )


@pytest.fixture
def no_socket() -> Generator[None]:
    """The live state is fed by the test, not over a WebSocket."""

    async def idle(self) -> None:
        return None

    with patch("custom_components.gexis.api.GexisPlayer.listen", idle):
        yield
