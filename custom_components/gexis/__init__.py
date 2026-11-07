"""The Gexis Player integration."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, service
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .api import GexisError, GexisPlayer
from .const import (
    ATTR_PAGE_ID,
    ATTR_SECONDS,
    ATTR_URL,
    CARD_FILE,
    DOMAIN,
    FRONTEND_URL,
    PAGE_MAX_S,
    PAGE_MIN_S,
    SERVICE_HIDE_PAGE,
    SERVICE_PRELOAD_PAGE,
    SERVICE_SHOW_PAGE,
)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.MEDIA_PLAYER,
    Platform.REMOTE,
    Platform.SELECT,
    Platform.SWITCH,
]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

#: ADR-0176: what a page needs - an http(s) address, a name, a time.
SHOW_PAGE_SCHEMA = {
    vol.Required(ATTR_URL): vol.All(cv.string, vol.Match(r"^https?://\S+$")),
    vol.Optional(ATTR_PAGE_ID): vol.All(cv.string, vol.Length(min=1, max=64)),
    vol.Optional(ATTR_SECONDS): vol.All(vol.Coerce(int), vol.Range(min=PAGE_MIN_S, max=PAGE_MAX_S)),
}
HIDE_PAGE_SCHEMA = {vol.Optional(ATTR_PAGE_ID): vol.All(cv.string, vol.Length(min=1, max=64))}
#: The page to keep loaded; empty or left out clears it.
PRELOAD_PAGE_SCHEMA = {vol.Optional(ATTR_URL): vol.Any(None, "", vol.All(cv.string, vol.Match(r"^https?://\S+$")))}

type GexisConfigEntry = ConfigEntry[GexisPlayer]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """**The card, served and added to the frontend** (ADR-0163 D1), once
    for every player: it is in the card picker with nothing to register.
    **And a page on the player's screen** (ADR-0176): three actions on the
    player's media player - show, hide, and the page to keep loaded."""
    service.async_register_platform_entity_service(
        hass, DOMAIN, SERVICE_SHOW_PAGE, entity_domain=MEDIA_PLAYER_DOMAIN,
        schema=SHOW_PAGE_SCHEMA, func="async_show_page",
    )
    service.async_register_platform_entity_service(
        hass, DOMAIN, SERVICE_HIDE_PAGE, entity_domain=MEDIA_PLAYER_DOMAIN,
        schema=HIDE_PAGE_SCHEMA, func="async_hide_page",
    )
    service.async_register_platform_entity_service(
        hass, DOMAIN, SERVICE_PRELOAD_PAGE, entity_domain=MEDIA_PLAYER_DOMAIN,
        schema=PRELOAD_PAGE_SCHEMA, func="async_preload_page",
    )
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
