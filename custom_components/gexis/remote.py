"""The D-pad for the player's screen, as a remote (ADR-0161 D7)."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GexisConfigEntry
from .api import KEYS, GexisError, GexisPlayer
from .entity import GexisEntity

#: The D-pad's keys, and Home, which is the route that already exists.
COMMANDS = (*KEYS, "home")


async def async_setup_entry(
    hass: HomeAssistant, entry: GexisConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GexisRemote(entry.runtime_data)])


class GexisRemote(GexisEntity, RemoteEntity):
    _attr_translation_key = "dpad"

    def __init__(self, player: GexisPlayer) -> None:
        super().__init__(player, "dpad")

    @property
    def available(self) -> bool:
        return super().available and self.player.status.get("screen") is True

    @property
    def is_on(self) -> bool:
        """On while the screen is lit, as the Screen switch."""
        return not (self.state_dict.get("panel") or {}).get("standby")

    async def _run(self, call) -> None:
        try:
            await call
        except GexisError as err:
            raise HomeAssistantError(f"{self.player.status.get('name')}: {err}") from err

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._run(self.player.standby(False))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._run(self.player.standby(True))

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        commands = list(command)
        unknown = [c for c in commands if c not in COMMANDS]
        if unknown:
            raise ServiceValidationError(
                f"Unknown command {', '.join(unknown)}: the D-pad takes {', '.join(COMMANDS)}"
            )
        repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        first = True
        for _ in range(repeats):
            for name in commands:
                if not first and delay:
                    await asyncio.sleep(delay)
                first = False
                await self._run(self.player.go("home") if name == "home" else self.player.key(name))
