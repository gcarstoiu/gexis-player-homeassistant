# Gexis Player for Home Assistant

Each [Gexis Player](https://github.com/gcarstoiu/gexis-player) on the home
network in Home Assistant, as a media player: what plays, with its artwork;
play, pause, next and previous; volume and mute; the source. On a player with
a screen, three switches as well: the screen (display standby), the Home
Assistant dashboard and the visualiser.

## What it needs

- Home Assistant 2026.3 or later.
- A Gexis Player release newer than 1.4.0. An older player is found, and asked
  to update first.

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
| Media player | Playing, paused or idle; title, artist, album, artwork, position. Play, pause, next and previous when the source playing offers them; shuffle and repeat where it has them; volume and mute, unless the output is fixed; the source, chosen from those that can take over. |
| Screen | On is lit; off is display standby. |
| Dashboard | Puts the player's Home Assistant dashboard up or takes it down. Unavailable until a dashboard address is set on the player (*Settings → Display → Home Assistant dashboard*). |
| Visualiser | Shows or hides the visualiser. |

The switches are unavailable on a player without a screen.

## Good to know

- The player changes nothing in Home Assistant. Its API is open to the home
  network with no login, as the player's own settings are.
- With Home Assistant's own *Lyrion Music Server* integration set up too, a
  player also shows there, as Lyrion's player. This integration covers every
  source and the screen.

## Licence

GPL-3.0-or-later, as Gexis Player.
