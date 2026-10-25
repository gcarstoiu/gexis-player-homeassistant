"""The Gexis Player integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .api import GexisError, GexisPlayer
from .const import CARD_FILE, DOMAIN, FRONTEND_URL

PLATFORMS = [Platform.BUTTON, Platform.MEDIA_PLAYER, Platform.REMOTE, Platform.SWITCH]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type GexisConfigEntry = ConfigEntry[GexisPlayer]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """**The card, served and added to the frontend** (ADR-0163 D1), once
    for every player: it is in the card picker with nothing to register."""
    if hass.http is None:  # no web server, as in tests
        return True
    from homeassistant.components.http import StaticPathConfig

    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL, str(Path(__file__).parent / "frontend"), True)]
    )
    if "frontend" in hass.config.components:
        from homeassistant.components.frontend import add_extra_js_url

        version = (await async_get_integration(hass, DOMAIN)).version
        add_extra_js_url(hass, f"{FRONTEND_URL}/{CARD_FILE}?v={version}")
    return True


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
