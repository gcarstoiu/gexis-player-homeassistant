"""The player as a media player: what plays, the transport, volume, the source."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import GexisConfigEntry
from .api import GexisError, GexisPlayer
from .const import DOMAIN
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
        if self._volume is not None:
            features |= (
                MediaPlayerEntityFeature.VOLUME_SET
                | MediaPlayerEntityFeature.VOLUME_STEP
                | MediaPlayerEntityFeature.VOLUME_MUTE
            )
        elif self._fixed_mute is not None:
            features |= MediaPlayerEntityFeature.VOLUME_MUTE
        # The player's groups (its ADR-0166): Home Assistant's own join.
        if self.player.status.get("multiroom"):
            features |= MediaPlayerEntityFeature.GROUPING
        return features

    def _entity_of(self, player_id: str) -> str | None:
        return er.async_get(self.hass).async_get_entity_id("media_player", DOMAIN, player_id)

    def _player_of(self, entity_id: str) -> str | None:
        entry = er.async_get(self.hass).async_get(entity_id)
        return entry.unique_id if entry is not None and entry.platform == DOMAIN else None

    @property
    def group_members(self) -> list[str] | None:
        """The group this player is in, the player that leads first - the
        players Home Assistant knows."""
        group = self.state_dict.get("group")
        if not group:
            return None
        members = [self._entity_of(m["id"]) for m in group.get("members") or []]
        return [m for m in members if m]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"available_controls": sorted(self._controls.get("available") or [])}

    @property
    def state(self) -> MediaPlayerState:
        if not self.state_dict.get("active"):
            return MediaPlayerState.IDLE
        transport = self._meta.get("transport")
        if transport == "playing":
            return MediaPlayerState.PLAYING
        if transport == "paused":
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
        """Shown, not chosen: a source is taken over from its own app."""
        active = self.state_dict.get("active")
        if not active:
            return None
        return next((s["name"] for s in self.state_dict.get("sources") or [] if s.get("id") == active), active)

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

    async def async_join_players(self, group_members: list[str]) -> None:
        """The players joined to this one's group: they stop what they play
        and play this one's music."""
        for entity_id in group_members:
            player_id = self._player_of(entity_id)
            if player_id is None:
                raise HomeAssistantError(f"{entity_id} is not a Gexis Player")
            if player_id != self.player.status.get("id"):
                await self._run(self.player.join(player_id))

    async def async_unjoin_player(self) -> None:
        """This player out of its group. The player that leads has no leave:
        unjoined, its group ends, and the music stays on it."""
        group = self.state_dict.get("group") or {}
        me = group.get("me")
        if not group:
            return
        if me is not None and group.get("leader") == me:
            await self._run(self.player.undo())
        else:
            await self._run(self.player.leave())
