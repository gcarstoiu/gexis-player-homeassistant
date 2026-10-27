"""The screen, the dashboard, the visualiser and the idle screen, on a player
with a screen; the equaliser, on any player (ADR-0163 16)."""

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
    #: From the player's whole state.
    is_on: Callable[[dict[str, Any]], bool]
    turn: Callable[[GexisPlayer, bool], Awaitable[None]]
    needs_screen: bool = True
    #: Only while the output in use has an equaliser (`/state`'s `equaliser`).
    needs_equaliser: bool = False
    needs_dashboard: bool = False
    #: Left out where the phone leaves it out: the visualiser on an output
    #: that cannot feed the meters, the idle screen while it is switched off.
    needs_meters: bool = False
    needs_idle: bool = False


def _panel(state: dict[str, Any]) -> dict[str, Any]:
    return state.get("panel") or {}


SWITCHES = (
    GexisSwitchDescription(
        key="screen",
        translation_key="screen",
        is_on=lambda state: not _panel(state).get("standby"),
        turn=lambda player, on: player.standby(not on),
    ),
    GexisSwitchDescription(
        key="dashboard",
        translation_key="dashboard",
        is_on=lambda state: bool((_panel(state).get("dashboard") or {}).get("shown")),
        turn=lambda player, on: player.dashboard(on),
        needs_dashboard=True,
    ),
    GexisSwitchDescription(
        key="visualiser",
        translation_key="visualiser",
        is_on=lambda state: bool(_panel(state).get("visualiser")),
        turn=lambda player, on: player.visualiser(on),
        needs_meters=True,
    ),
    GexisSwitchDescription(
        key="idle",
        translation_key="idle_screen",
        is_on=lambda state: bool(_panel(state).get("idle")),
        turn=lambda player, on: player.idle(on),
        needs_idle=True,
    ),
    GexisSwitchDescription(
        key="equaliser",
        translation_key="equaliser",
        is_on=lambda state: bool((state.get("equaliser") or {}).get("on")),
        turn=lambda player, on: player.set_equaliser({"on": on}),
        needs_screen=False,
        needs_equaliser=True,
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
        description = self.entity_description
        if not super().available:
            return False
        if description.needs_screen and self.player.status.get("screen") is not True:
            return False
        if description.needs_equaliser and not self.state_dict.get("equaliser"):
            return False
        if description.needs_meters and self.state_dict.get("meters") is False:
            return False
        # A player before the field says nothing: the idle screen is offered.
        if description.needs_idle and self.player.status.get("idle_screen") is False:
            return False
        return self.player.dashboard_set or not description.needs_dashboard

    @property
    def is_on(self) -> bool:
        return self.entity_description.is_on(self.state_dict)

    async def _turn(self, on: bool) -> None:
        try:
            await self.entity_description.turn(self.player, on)
        except GexisError as err:
            raise HomeAssistantError(f"{self.player.status.get('name')}: {err}") from err

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._turn(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._turn(False)
