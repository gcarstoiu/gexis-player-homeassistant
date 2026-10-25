"""The card: served by the integration and added to the frontend (ADR-0163 D1)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.gexis.const import CARD_FILE, DOMAIN, FRONTEND_URL

FRONTEND = Path(__file__).parents[1] / "custom_components" / "gexis" / "frontend"


async def test_the_card_is_served_and_loaded_once(hass: HomeAssistant) -> None:
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()
    hass.config.components.add("frontend")
    with patch("homeassistant.components.frontend.add_extra_js_url") as add:
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
    (paths,) = hass.http.async_register_static_paths.await_args.args
    assert [(p.url_path, Path(p.path)) for p in paths] == [(FRONTEND_URL, FRONTEND)]
    version = json.loads((FRONTEND.parent / "manifest.json").read_text())["version"]
    add.assert_called_once_with(hass, f"{FRONTEND_URL}/{CARD_FILE}?v={version}")


async def test_without_a_web_server_nothing_is_served(hass: HomeAssistant) -> None:
    assert hass.http is None
    with patch("homeassistant.components.frontend.add_extra_js_url") as add:
        assert await async_setup_component(hass, DOMAIN, {})
    add.assert_not_called()


def test_the_card_and_its_fonts_are_there() -> None:
    card = (FRONTEND / CARD_FILE).read_text()
    assert "customElements.define('gexis-player-card'" in card
    for font in ("NunitoSans-Variable.woff2", "IBMPlexMono-Regular.woff2", "IBMPlexMono-SemiBold.woff2"):
        assert (FRONTEND / "fonts" / font).is_file()
        assert font in card
    version = json.loads((FRONTEND.parent / "manifest.json").read_text())["version"]
    assert f"const VERSION = '{version}'" in card, "the card's version follows the manifest's"
