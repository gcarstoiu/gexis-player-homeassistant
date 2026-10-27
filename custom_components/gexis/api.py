"""A Gexis Player's HTTP API: its live state over a WebSocket, and commands."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import aiohttp

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=10)
RETRY_MAX_S = 30
LOOPBACK = {"127.0.0.1", "localhost", "::1"}


class GexisError(Exception):
    """The player could not be reached, or refused a command."""


class TooOld(GexisError):
    """The player gives no lasting id: an older release, or not a Raspberry Pi."""


#: ADR-0161 D6: the D-pad's keys, as `POST /panel/key` takes them.
KEYS = ("up", "down", "left", "right", "ok", "back")
UPDATE_FOR_KEYS = "This player is too old for the D-pad. Update it first: Settings → System → Software update on the player."
UPDATE_FOR_EQUALISER = "This player is too old for the equaliser. Update it first: Settings → System → Software update on the player."


class GexisPlayer:
    """One player, reached at `http://host:port`."""

    def __init__(self, session: aiohttp.ClientSession, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.base = f"http://{host}:{port}"
        self.status: dict[str, Any] = {}
        self.state: dict[str, Any] | None = None
        self.dashboard_set = False
        self._session = session
        self._listeners: list[Callable[[], None]] = []
        self._revision: int | None = None

    @property
    def connected(self) -> bool:
        return self.state is not None

    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    async def fetch_status(self) -> dict[str, Any]:
        """`GET /player/status`: name, lasting id, whether it has a screen."""
        try:
            async with self._session.get(f"{self.base}/player/status", timeout=TIMEOUT) as r:
                r.raise_for_status()
                status = await r.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise GexisError(str(err)) from err
        if not isinstance(status, dict) or not status.get("id"):
            raise TooOld
        self.status = status
        return status

    async def _fetch_dashboard(self) -> None:
        try:
            async with self._session.get(f"{self.base}/panel/dashboard", timeout=TIMEOUT) as r:
                r.raise_for_status()
                check = await r.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError):
            return
        self.dashboard_set = bool(isinstance(check, dict) and check.get("url"))

    async def _on_state(self, state: dict[str, Any]) -> None:
        revision = state.get("settings_revision")
        if revision != self._revision:
            # A setting changed: the name, headless, the dashboard's address.
            self._revision = revision
            try:
                await self.fetch_status()
            except GexisError:
                pass
            await self._fetch_dashboard()
        self.state = state
        self._notify()

    async def listen(self) -> None:
        """Follow `/state` until cancelled, reconnecting after a drop."""
        delay = 1
        while True:
            try:
                async with self._session.ws_connect(f"{self.base}/state", heartbeat=30) as ws:
                    delay = 1
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await self._on_state(msg.json())
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
            except (aiohttp.ClientError, TimeoutError, ValueError) as err:
                _LOGGER.debug("%s: %s", self.base, err)
            if self.state is not None:
                self.state = None
                self._revision = None
                self._notify()
            await asyncio.sleep(delay)
            delay = min(delay * 2, RETRY_MAX_S)

    def artwork(self, url: str | None) -> str | None:
        """An artwork URL Home Assistant can fetch: one on the player's own
        Lyrion server names the loopback address, which is the player."""
        if not url:
            return None
        if url.startswith("/"):
            return f"{self.base}{url}"
        parts = urlsplit(url)
        if parts.hostname in LOOPBACK:
            netloc = self.host if parts.port is None else f"{self.host}:{parts.port}"
            return urlunsplit(parts._replace(netloc=netloc))
        return url

    async def _post(self, path: str, body: dict[str, Any] | None = None, missing: str | None = None) -> None:
        await self._send("POST", path, body, missing)

    async def _send(self, method: str, path: str, body: dict[str, Any] | None = None, missing: str | None = None) -> None:
        """`missing`: what to say when the player has no such route (404) - a
        release from before it."""
        try:
            async with self._session.request(method, f"{self.base}{path}", json=body, timeout=TIMEOUT) as r:
                if r.status == 404 and missing:
                    raise GexisError(missing)
                if r.status >= 400:
                    try:
                        error = (await r.json(content_type=None)).get("error")
                    except (ValueError, AttributeError):
                        error = None
                    raise GexisError(error or f"HTTP {r.status}")
        except (aiohttp.ClientError, TimeoutError) as err:
            raise GexisError(str(err)) from err

    async def transport(self, command: str, body: dict[str, Any] | None = None) -> None:
        await self._post(f"/transport/{command}", body)

    async def seek(self, position: float) -> None:
        """To `position` seconds into the track (ADR-0164 C2)."""
        await self._post("/transport/seek", {"position": position})

    async def set_equaliser(self, changes: dict[str, Any]) -> None:
        """`on` or `sel`, for the output in use (ADR-0162 D9)."""
        await self._send("PUT", "/equaliser", changes, missing=UPDATE_FOR_EQUALISER)

    async def set_volume(self, percent: int) -> None:
        await self._post("/volume", {"percent": percent})

    async def set_mute(self, muted: bool) -> None:
        await self._post("/volume/mute", {"muted": muted})

    async def go(self, to: str) -> None:
        await self._post(f"/panel/go/{to}")

    async def key(self, key: str) -> None:
        """A D-pad key on the player's screen (ADR-0161 D6)."""
        await self._post("/panel/key", {"key": key}, missing=UPDATE_FOR_KEYS)

    async def standby(self, on: bool) -> None:
        await self._post(f"/panel/standby/{'on' if on else 'off'}")

    async def dashboard(self, show: bool) -> None:
        await self._post(f"/panel/dashboard/{'show' if show else 'hide'}")

    async def idle(self, show: bool) -> None:
        """The idle screen up or down, as the phone's Idle does (ADR-0101)."""
        await self._post(f"/panel/idle/{'show' if show else 'hide'}")

    async def visualiser(self, show: bool) -> None:
        await self._post(f"/peppy/{'show' if show else 'hide'}")
