"""The screen, the dashboard and the visualiser, on a player with a screen."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GexisConfigEntry
from .api import GexisError, GexisPlayer
from .entity import GexisEntity


@dataclass(frozen=True, kw_only=True)
class GexisSwitchDescription(SwitchEntityDescription):
    is_on: Callable[[dict[str, Any]], bool]
    turn: Callable[[GexisPlayer, bool], Awaitable[None]]
    needs_dashboard: bool = False


SWITCHES = (
    GexisSwitchDescription(
        key="screen",
        translation_key="screen",
        is_on=lambda panel: not panel.get("standby"),
        turn=lambda player, on: player.standby(not on),
    ),
    GexisSwitchDescription(
        key="dashboard",
        translation_key="dashboard",
        is_on=lambda panel: bool((panel.get("dashboard") or {}).get("shown")),
        turn=lambda player, on: player.dashboard(on),
        needs_dashboard=True,
    ),
    GexisSwitchDescription(
        key="visualiser",
        translation_key="visualiser",
        is_on=lambda panel: bool(panel.get("visualiser")),
        turn=lambda player, on: player.visualiser(on),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: GexisConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(GexisSwitch(entry.runtime_data, description) for description in SWITCHES)


class GexisSwitch(GexisEntity, SwitchEntity):
    entity_description: GexisSwitchDescription

    def __init__(self, player: GexisPlayer, description: GexisSwitchDescription) -> None:
        super().__init__(player, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if not super().available or self.player.status.get("screen") is not True:
            return False
        return self.player.dashboard_set or not self.entity_description.needs_dashboard

    @property
    def is_on(self) -> bool:
        return self.entity_description.is_on(self.state_dict.get("panel") or {})

    async def _turn(self, on: bool) -> None:
        try:
            await self.entity_description.turn(self.player, on)
        except GexisError as err:
            raise HomeAssistantError(f"{self.player.status.get('name')}: {err}") from err

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._turn(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._turn(False)
