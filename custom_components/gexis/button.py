"""Home, Now playing and Lyrics on the player's screen."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GexisConfigEntry
from .api import GexisError, GexisPlayer
from .entity import GexisEntity


@dataclass(frozen=True, kw_only=True)
class GexisButtonDescription(ButtonEntityDescription):
    #: Now Playing and Lyrics exist only while a source is active.
    needs_source: bool = True


BUTTONS = (
    GexisButtonDescription(key="home", translation_key="home", needs_source=False),
    GexisButtonDescription(key="now", translation_key="now"),
    GexisButtonDescription(key="lyrics", translation_key="lyrics"),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: GexisConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(GexisButton(entry.runtime_data, description) for description in BUTTONS)


class GexisButton(GexisEntity, ButtonEntity):
    entity_description: GexisButtonDescription

    def __init__(self, player: GexisPlayer, description: GexisButtonDescription) -> None:
        super().__init__(player, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if not super().available or self.player.status.get("screen") is not True:
            return False
        return bool(self.state_dict.get("active")) or not self.entity_description.needs_source

    async def async_press(self) -> None:
        try:
            await self.player.go(self.entity_description.key)
        except GexisError as err:
            raise HomeAssistantError(f"{self.player.status.get('name')}: {err}") from err
