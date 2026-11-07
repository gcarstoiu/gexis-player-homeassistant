"""Whether a page from Home Assistant is on the player's screen (ADR-0176)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GexisConfigEntry
from .api import GexisPlayer
from .entity import GexisEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: GexisConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GexisPage(entry.runtime_data)])


class GexisPage(GexisEntity, BinarySensorEntity):
    """On while a page shows. Unavailable on a player without a screen, or
    while its *Pages from Home Assistant* is off, so a dashboard or an
    automation can tell where a page can be shown."""

    _attr_translation_key = "page"

    def __init__(self, player: GexisPlayer) -> None:
        super().__init__(player, "page")

    @property
    def _page(self) -> dict[str, Any]:
        return (self.state_dict.get("panel") or {}).get("page") or {}

    @property
    def available(self) -> bool:
        return super().available and self.player.status.get("screen") is True and self.player.pages

    @property
    def is_on(self) -> bool:
        return self._page.get("shown") is True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        closed = self._page.get("closed") or {}
        return {
            "page_id": self._page.get("id"),
            "until": self._page.get("until"),
            "closed_id": closed.get("id"),
            "closed_by": closed.get("by"),
        }
