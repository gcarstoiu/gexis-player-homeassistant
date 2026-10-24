"""The Gexis Player integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GexisError, GexisPlayer

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SWITCH]

type GexisConfigEntry = ConfigEntry[GexisPlayer]


async def async_setup_entry(hass: HomeAssistant, entry: GexisConfigEntry) -> bool:
    player = GexisPlayer(async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_PORT])
    try:
        await player.fetch_status()
    except GexisError as err:
        raise ConfigEntryNotReady(f"{player.base} did not answer") from err
    entry.runtime_data = player
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_create_background_task(hass, player.listen(), f"gexis {player.base}")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GexisConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
