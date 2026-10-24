"""What every Gexis Player entity shares: the device and the live state."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .api import GexisPlayer
from .const import DOMAIN


class GexisEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, player: GexisPlayer, key: str | None) -> None:
        self.player = player
        player_id = player.status["id"]
        self._attr_unique_id = player_id if key is None else f"{player_id}-{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, player_id)},
            name=player.status.get("name"),
            manufacturer="Gexis",
            model="Gexis Player",
            configuration_url=f"{player.base}/",
        )

    @property
    def state_dict(self) -> dict[str, Any]:
        return self.player.state or {}

    @property
    def available(self) -> bool:
        return self.player.connected

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.player.subscribe(self._on_change))

    def _on_change(self) -> None:
        self.async_write_ha_state()
