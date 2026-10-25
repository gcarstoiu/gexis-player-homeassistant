# Gexis Player for Home Assistant

Each [Gexis Player](https://github.com/gcarstoiu/gexis-player) on the home
network in Home Assistant, as a media player: what plays, with its artwork;
play, pause, next and previous; volume and mute; the source playing. On a
player with a screen, three switches as well - the screen (display standby),
the Home Assistant dashboard and the visualiser - and three buttons: Home,
Now playing and Lyrics.

## What it needs

- Home Assistant 2026.3 or later.
- Gexis Player 1.5.0 or later (on the Testing channel from 24 October 2026).
  An older player is found, and asked to update first.

## Installing

With HACS: add `https://github.com/gcarstoiu/gexis-player-homeassistant` under
*Custom repositories*, type *Integration*, download *Gexis Player*, and restart
Home Assistant.

By hand: copy `custom_components/gexis` into Home Assistant's
`custom_components` folder and restart Home Assistant.

## Adding a player

Players on the same network show under *Settings → Devices & services* as
discovered; confirm each one. A player that does not show can be added by its
address: *Add integration → Gexis Player*, then its name on the network (for
example `livingroom.local`) and port 8090.

## What Home Assistant gets

| Entity | What it does |
|---|---|
| Media player | Playing, paused or idle; title, artist, album, artwork, position. Play, pause, next and previous when the source playing offers them; shuffle and repeat where it has them; volume and mute, unless the output is fixed; the source playing (each source is taken over from its own app, as on the player). |
| Screen | On is lit; off is display standby. |
| Dashboard | Puts the player's Home Assistant dashboard up or takes it down. Unavailable until a dashboard address is set on the player (*Settings → Display → Home Assistant dashboard*). |
| Visualiser | Shows or hides the visualiser. |
| Home | Opens Home on the player's screen. |
| Now playing, Lyrics | Opens Now Playing or the lyrics on the player's screen. Unavailable while no source is active. |

The switches and buttons are unavailable on a player without a screen.

## Good to know

- The player changes nothing in Home Assistant. Its API is open to the home
  network with no login, as the player's own settings are.
- With Home Assistant's own *Lyrion Music Server* integration set up too, a
  player also shows there, as Lyrion's player. This integration covers every
  source and the screen.

## Licence

GPL-3.0-or-later, as Gexis Player.
