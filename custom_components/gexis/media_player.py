"""The player as a media player: what plays, the transport, volume, the source."""

from __future__ import annotations

import base64
from datetime import datetime
import json
from typing import Any
from urllib.parse import quote, unquote

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaClass,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode,
    SearchMedia,
    SearchMediaQuery,
)
from homeassistant.components.media_player.errors import BrowseError
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import GexisConfigEntry
from .api import GexisError, GexisPlayer
from .entity import GexisEntity

#: A position further than this from where it should be is a seek.
DRIFT_S = 2.5

COMMAND_FEATURES = {
    "play": MediaPlayerEntityFeature.PLAY,
    "pause": MediaPlayerEntityFeature.PAUSE,
    "next": MediaPlayerEntityFeature.NEXT_TRACK,
    "previous": MediaPlayerEntityFeature.PREVIOUS_TRACK,
    "shuffle": MediaPlayerEntityFeature.SHUFFLE_SET,
    "repeat": MediaPlayerEntityFeature.REPEAT_SET,
    "seek": MediaPlayerEntityFeature.SEEK,
}
REPEAT = {"off": RepeatMode.OFF, "all": RepeatMode.ALL, "one": RepeatMode.ONE}

#: ADR-0180: the player's internet radio in Home Assistant's media browser.
#: Folders are `gexis:radio/<what>`; a favourite is `gexis:favourite/<id>`;
#: a station from a list carries itself, `gexis:station/<base64 JSON>`, so a
#: play from an automation still works after a restart.
RADIO = "gexis:radio"
FAVOURITE = "gexis:favourite/"
STATION = "gexis:station/"
LOGO = "/stations/logo/"
#: What a station carries back to the player when it is played.
STATION_KEYS = ("id", "name", "url", "logo", "country", "countrycode", "codec", "bitrate", "hls", "listed")
FOLDERS = (("favourites", "Favourites"), ("popular", "Popular here"), ("genres", "By genre"),
           ("countries", "By country"), ("languages", "By language"))


def station_id(station: dict[str, Any]) -> str:
    data = json.dumps({k: station[k] for k in STATION_KEYS if station.get(k) is not None}, separators=(",", ":"))
    return STATION + base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")


def station_of(content_id: str) -> dict[str, Any] | None:
    try:
        text = content_id[len(STATION):]
        data = json.loads(base64.urlsafe_b64decode(text + "=" * (-len(text) % 4)))
    except (ValueError, TypeError):
        return None
    return data if isinstance(data, dict) and data.get("id") and data.get("url") else None


def meta(station: dict[str, Any]) -> str:
    """*Germany · MP3 · 128 kb/s*, as the player's rows say it."""
    parts = [station.get("country"), station.get("codec"),
             f"{station['bitrate']} kb/s" if station.get("bitrate") else None]
    return " · ".join(p for p in parts if p)


async def async_setup_entry(
    hass: HomeAssistant, entry: GexisConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([GexisMediaPlayer(entry.runtime_data)])


class GexisMediaPlayer(GexisEntity, MediaPlayerEntity):
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_media_content_type = MediaType.MUSIC
    _attr_media_image_remotely_accessible = False

    def __init__(self, player: GexisPlayer) -> None:
        super().__init__(player, None)
        self._position: float | None = None
        self._position_at: datetime | None = None
        self._anchor: tuple[Any, ...] | None = None

    @property
    def _meta(self) -> dict[str, Any]:
        return self.state_dict.get("metadata") or {}

    @property
    def _controls(self) -> dict[str, Any]:
        return self.state_dict.get("controls") or {}

    @property
    def _source_controls(self) -> list[str]:
        """**What the source playing has**, as the player shows it (ADR-0037
        §3): a control it has but cannot use now (Next at the end of the
        queue) stays, and `available_controls` says which work now."""
        active = self.state_dict.get("active")
        if not active:
            return []
        source = (self.state_dict.get("capabilities") or {}).get(active) or {}
        return source.get("controls") or self._controls.get("available") or []

    @property
    def _volume(self) -> dict[str, Any] | None:
        if self.state_dict.get("fixed_output"):
            return None
        return self.state_dict.get("volume")

    @property
    def _fixed_mute(self) -> bool | None:
        """**Mute with Fixed volume** (ADR-0165): None where the output has no
        control of its own to silence, or the volume is not Fixed."""
        if not self.state_dict.get("fixed_output"):
            return None
        return self.state_dict.get("fixed_mute")

    def _on_change(self) -> None:
        self._follow_position()
        super()._on_change()

    def _follow_position(self) -> None:
        """Move the position's timestamp only on a jump, a new track or a
        pause, so a playing track does not write a state every second."""
        meta = self._meta
        position = meta.get("position")
        if position is None:
            self._position = self._position_at = self._anchor = None
            return
        now = dt_util.utcnow()
        anchor = (meta.get("track_id"), meta.get("title"), meta.get("transport"))
        if self._anchor == anchor and self._position is not None and self._position_at is not None:
            expected = self._position
            if meta.get("transport") == "playing":
                expected += (now - self._position_at).total_seconds()
            if abs(position - expected) < DRIFT_S:
                return
        self._position, self._position_at, self._anchor = position, now, anchor

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        features = MediaPlayerEntityFeature(0)
        for command in self._source_controls:
            features |= COMMAND_FEATURES.get(command, MediaPlayerEntityFeature(0))
        if self.player.radio:
            # ADR-0180 item 10: the favourites as sources, the directory in
            # the media browser, searched by name.
            features |= (MediaPlayerEntityFeature.BROWSE_MEDIA | MediaPlayerEntityFeature.PLAY_MEDIA
                         | MediaPlayerEntityFeature.SEARCH_MEDIA)
            if self.player.favourites:
                features |= MediaPlayerEntityFeature.SELECT_SOURCE
        if self._volume is not None:
            features |= (
                MediaPlayerEntityFeature.VOLUME_SET
                | MediaPlayerEntityFeature.VOLUME_STEP
                | MediaPlayerEntityFeature.VOLUME_MUTE
            )
        elif self._fixed_mute is not None:
            features |= MediaPlayerEntityFeature.VOLUME_MUTE
        return features

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attributes: dict[str, Any] = {"available_controls": sorted(self._controls.get("available") or [])}
        radio = self.state_dict.get("radio")
        if self.player.radio and isinstance(radio, dict):
            # For the card's Radio view: which station plays, and whether it
            # is a favourite (the heart).
            station = radio.get("station") or {}
            attributes["radio"] = {"station": station.get("id"), "favourite": station.get("favourite") is True,
                                   "state": radio.get("state")}
        return attributes

    @property
    def state(self) -> MediaPlayerState:
        if not self.state_dict.get("active"):
            return MediaPlayerState.IDLE
        transport = self._meta.get("transport")
        if transport == "playing":
            return MediaPlayerState.PLAYING
        if transport == "paused":
            return MediaPlayerState.PAUSED
        if (transport == "stopped" and self.state_dict.get("active") == "radio"
                and (self.state_dict.get("radio") or {}).get("station")):
            # A station stops rather than pauses (ADR-0180), and the player
            # keeps it: Play starts it again. So it shows as paused, with
            # Play, not as nothing playing (George, 2026-11-14).
            return MediaPlayerState.PAUSED
        return MediaPlayerState.IDLE

    @property
    def media_title(self) -> str | None:
        return self._meta.get("title")

    @property
    def media_artist(self) -> str | None:
        return self._meta.get("artist")

    @property
    def media_album_name(self) -> str | None:
        return self._meta.get("album")

    @property
    def media_duration(self) -> float | None:
        return self._meta.get("duration")

    @property
    def media_position(self) -> float | None:
        return self._position

    @property
    def media_position_updated_at(self) -> datetime | None:
        return self._position_at

    @property
    def media_image_url(self) -> str | None:
        return self.player.artwork(self._meta.get("artwork"))

    @property
    def volume_level(self) -> float | None:
        volume = self._volume
        return None if not volume or volume.get("percent") is None else volume["percent"] / 100

    @property
    def is_volume_muted(self) -> bool | None:
        volume = self._volume
        if volume:
            return volume.get("muted")
        return self._fixed_mute

    @property
    def source(self) -> str | None:
        """Shown, not chosen: a source is taken over from its own app - but
        an internet radio favourite is chosen here, and is its own name."""
        active = self.state_dict.get("active")
        if not active:
            return None
        station = (self.state_dict.get("radio") or {}).get("station") or {}
        if active == "radio" and station.get("favourite"):
            return station.get("name")
        return next((s["name"] for s in self.state_dict.get("sources") or [] if s.get("id") == active), active)

    @property
    def source_list(self) -> list[str] | None:
        """**The player's internet radio favourites** (ADR-0180 item 10), in
        its order; the other sources are taken over from their own apps."""
        if not self.player.radio or not self.player.favourites:
            return None
        return [f["name"] for f in self.player.favourites]

    @property
    def shuffle(self) -> bool | None:
        return self._controls.get("shuffle")

    @property
    def repeat(self) -> RepeatMode | None:
        return REPEAT.get(self._controls.get("repeat"))

    async def _run(self, call) -> None:
        try:
            await call
        except GexisError as err:
            raise HomeAssistantError(f"{self.player.status.get('name')}: {err}") from err

    async def async_media_play(self) -> None:
        await self._run(self.player.transport("play"))

    async def async_media_pause(self) -> None:
        await self._run(self.player.transport("pause"))

    async def async_media_next_track(self) -> None:
        await self._run(self.player.transport("next"))

    async def async_media_previous_track(self) -> None:
        await self._run(self.player.transport("previous"))

    async def async_set_shuffle(self, shuffle: bool) -> None:
        await self._run(self.player.transport("shuffle", {"on": shuffle}))

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        await self._run(self.player.transport("repeat", {"mode": repeat.value}))

    async def async_set_volume_level(self, volume: float) -> None:
        await self._run(self.player.set_volume(round(volume * 100)))

    async def async_mute_volume(self, mute: bool) -> None:
        await self._run(self.player.set_mute(mute))

    async def async_media_seek(self, position: float) -> None:
        await self._run(self.player.seek(position))

    # ADR-0180: internet radio - the favourites, the media browser, search.

    async def async_select_source(self, source: str) -> None:
        favourite = next((f for f in self.player.favourites if f.get("name") == source), None)
        if favourite is None:
            raise HomeAssistantError(f"{source} is not one of the player's favourite stations")
        await self._run(self.player.play_favourite(favourite["id"]))

    async def async_play_media(self, media_type: MediaType | str, media_id: str, **kwargs: Any) -> None:
        if media_id.startswith(FAVOURITE):
            await self._run(self.player.play_favourite(unquote(media_id[len(FAVOURITE):])))
            return
        station = station_of(media_id) if media_id.startswith(STATION) else None
        if station is None:
            raise HomeAssistantError(f"Not a station the player knows: {media_id}")
        await self._run(self.player.play_station(station))

    async def async_radio_favourite(self, favourite: bool) -> None:
        """The heart: the station playing now becomes a favourite, or stops
        being one."""
        station = (self.state_dict.get("radio") or {}).get("station")
        if self.state_dict.get("active") != "radio" or not station:
            raise HomeAssistantError("No internet radio station is playing")
        if favourite:
            await self._run(self.player.add_favourite({k: station[k] for k in STATION_KEYS if k in station}))
        else:
            await self._run(self.player.remove_favourite(station["id"]))

    def _station_item(self, station: dict[str, Any], content_id: str) -> BrowseMedia:
        logo = station.get("logo")
        thumbnail = None
        if isinstance(logo, str) and logo.startswith(LOGO):
            # Through Home Assistant's own proxy: a dashboard over https
            # cannot show a picture from the player's http address.
            thumbnail = self.get_browse_image_url(MediaType.CHANNEL, content_id, logo[len(LOGO):])
        return BrowseMedia(title=station.get("name") or "", media_class=MediaClass.CHANNEL,
                           media_content_id=content_id, media_content_type=MediaType.CHANNEL,
                           can_play=True, can_expand=False, thumbnail=thumbnail)

    def _folder(self, what: str, title: str, children: list[BrowseMedia] | None = None,
                media_class: MediaClass = MediaClass.DIRECTORY) -> BrowseMedia:
        return BrowseMedia(title=title, media_class=media_class, media_content_id=f"{RADIO}/{what}" if what else RADIO,
                           media_content_type="gexis_radio", can_play=False, can_expand=True,
                           children=children, children_media_class=MediaClass.CHANNEL)

    async def _list(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            return await self.player.stations(path, params)
        except GexisError as err:
            raise BrowseError(str(err)) from err

    async def async_browse_media(self, media_content_type: MediaType | str | None = None,
                                 media_content_id: str | None = None) -> BrowseMedia:
        if not self.player.radio:
            raise BrowseError("Internet radio is switched off on the player")
        what = (media_content_id or RADIO)[len(RADIO):].lstrip("/")
        if what == "":
            return self._folder("", "Internet radio", [self._folder(key, title) for key, title in FOLDERS])
        if what == "favourites":
            return self._folder(what, "Favourites", [
                self._station_item(f, FAVOURITE + quote(f["id"], safe="")) for f in self.player.favourites])
        if what == "popular":
            body = await self._list("/popular")
            return self._folder(what, "Popular here", [self._station_item(s, station_id(s)) for s in body.get("stations", [])])
        branches = {"genres": ("/genres", "genres", "genre", "By genre"),
                    "countries": ("/countries", "countries", "country", "By country"),
                    "languages": ("/languages", "languages", "language", "By language")}
        if what in branches:
            path, key, single, title = branches[what]
            body = await self._list(path)
            children = []
            for row in body.get(key, []):
                value = row.get("code") if single == "country" else row.get("name")
                if not value:
                    continue
                children.append(self._folder(f"{single}/{quote(value, safe='')}", row.get("name") or value,
                                             media_class=MediaClass.GENRE if single == "genre" else MediaClass.DIRECTORY))
            return self._folder(what, title, children)
        single, _, value = what.partition("/")
        if single in ("genre", "country", "language") and value:
            body = await self._list("/list", {single: unquote(value)})
            return self._folder(what, unquote(value), [self._station_item(s, station_id(s)) for s in body.get("stations", [])])
        raise BrowseError(f"Nothing to browse at {media_content_id}")

    async def async_search_media(self, query: SearchMediaQuery) -> SearchMedia:
        try:
            body = await self.player.stations("/search", {"q": query.search_query})
        except GexisError as err:
            raise HomeAssistantError(str(err)) from err
        return SearchMedia(result=[self._station_item(s, station_id(s)) for s in body.get("stations", [])])

    def card_radio(self) -> dict[str, Any]:
        """**What the card's Radio view draws** (design/source/31, C01-C06):
        the favourites in the player's order - each with its line, its logo
        through Home Assistant's proxy, and what plays it - and which plays."""
        favourites = []
        for f in self.player.favourites:
            content_id = FAVOURITE + quote(f["id"], safe="")
            logo = f.get("logo")
            favourites.append({
                "id": f["id"], "name": f["name"], "meta": meta(f), "content_id": content_id,
                "thumbnail": self.get_browse_image_url(MediaType.CHANNEL, content_id, logo[len(LOGO):])
                if isinstance(logo, str) and logo.startswith(LOGO) else None,
            })
        radio = self.state_dict.get("radio") or {}
        station = radio.get("station") or {}
        playing = station.get("id") if self.state_dict.get("active") == "radio" else None
        return {"enabled": self.player.radio, "favourites": favourites, "playing": playing,
                "state": radio.get("state")}

    async def async_get_browse_image(self, media_content_type: MediaType | str, media_content_id: str,
                                     media_image_id: str | None = None) -> tuple[bytes | None, str | None]:
        if not media_image_id:
            return None, None
        found = await self.player.logo(media_image_id)
        return found if found else (None, None)

    # ADR-0176: a page of Home Assistant's on the player's screen, for a while.
    async def async_show_page(self, url: str, id: str | None = None, seconds: int | None = None) -> None:
        await self._run(self.player.show_page(url, id, seconds))

    async def async_hide_page(self, id: str | None = None) -> None:
        await self._run(self.player.hide_page(id))

    async def async_preload_page(self, url: str | None = None) -> None:
        await self._run(self.player.preload_page(url))
