"""Constants for the Gexis Player integration."""

DOMAIN = "gexis"
DEFAULT_PORT = 8090

#: Where the card and its fonts are served (ADR-0163 D1).
FRONTEND_URL = "/gexis/frontend"
CARD_FILE = "gexis-player-card.js"

#: ADR-0176: a page from Home Assistant on the player's screen, for a while.
SERVICE_SHOW_PAGE = "show_page"
SERVICE_HIDE_PAGE = "hide_page"
#: The amendment: one page kept loaded and hidden, so showing it is at once.
SERVICE_PRELOAD_PAGE = "preload_page"
ATTR_URL = "url"
ATTR_PAGE_ID = "id"
ATTR_SECONDS = "seconds"
#: As the player takes them: 10 s to an hour.
PAGE_MIN_S = 10
PAGE_MAX_S = 3600
