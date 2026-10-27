"""The equaliser's setting, for the output in use (ADR-0163 16)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GexisConfigEntry
from .api import GexisError, GexisPlayer
from .entity import GexisEntity

#: Where moving a band leads; never chosen (ADR-0162).
CUSTOM = "custom"


async def async_setup_entry(
    hass: HomeAssistant, entry: GexisConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GexisEqualiserSetting(entry.runtime_data)])


class GexisEqualiserSetting(GexisEntity, SelectEntity):
    """The presets, then the owner's; *Custom* only while it is the one in use."""

    _attr_translation_key = "equaliser_setting"

    def __init__(self, player: GexisPlayer) -> None:
        super().__init__(player, "equaliser_setting")

    @property
    def _eq(self) -> dict[str, Any]:
        return self.state_dict.get("equaliser") or {}

    @property
    def _settings(self) -> list[dict[str, Any]]:
        return [*(self._eq.get("presets") or []), *(self._eq.get("own") or [])]

    @property
    def available(self) -> bool:
        return super().available and bool(self._eq)

    @property
    def options(self) -> list[str]:
        names = [s["name"] for s in self._settings]
        return ["Custom", *names] if self._eq.get("sel") == CUSTOM else names

    @property
    def current_option(self) -> str | None:
        sel = self._eq.get("sel")
        if sel == CUSTOM:
            return "Custom"
        return next((s["name"] for s in self._settings if s["key"] == sel), None)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Which are presets and which the owner's, for the card's row."""
        return {
            "presets": [p["name"] for p in self._eq.get("presets") or []],
            "own": [o["name"] for o in self._eq.get("own") or []],
        }

    async def async_select_option(self, option: str) -> None:
        key = next((s["key"] for s in self._settings if s["name"] == option), None)
        if key is None:
            raise ServiceValidationError(f"{option} is not a setting to choose: Custom comes from moving a band")
        try:
            await self.player.set_equaliser({"sel": key})
        except GexisError as err:
            raise HomeAssistantError(f"{self.player.status.get('name')}: {err}") from err
