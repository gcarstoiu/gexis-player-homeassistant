# Gexis Player for Home Assistant

Each [Gexis Player](https://github.com/gcarstoiu/gexis-player) on the home
network in Home Assistant, as a media player: what plays, with its artwork;
play, pause, next and previous; volume and mute; the source playing. On a
player with a screen, three switches as well - the screen (display standby),
the Home Assistant dashboard and the visualiser - three buttons (Home, Now
playing and Lyrics) and a D-pad. And a card for dashboards, for every
player in the home.

## What it needs

- Home Assistant 2026.3 or later.
- Gexis Player 1.5.0 or later.
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
| D-pad | A remote for the player's screen: `remote.send_command` with `up`, `down`, `left`, `right`, `ok`, `back` or `home`, with `num_repeats` and `delay_secs`. On while the screen is lit; turning it off or on is the screen's standby. Needs the next Gexis Player release; an older player is asked to update. |

The switches, buttons and D-pad are unavailable on a player without a screen.

## The card

*Gexis Player* comes with the integration, with nothing to install or
register. It goes on a dashboard that is edited by hand; Home Assistant's new
*Overview* takes favourite entities, not cards:

1. *Settings → Dashboards → Add dashboard → New dashboard from scratch*, if
   there is no such dashboard yet, and open it.
2. The pencil, then *+* in a section.
3. The *By card* tab (*By entity* offers only Home Assistant's own cards),
   and search for *Gexis*.
4. *Gexis Player*, then *Save* and *Done*.

It shows one player at a time, with
a switcher to the others; what plays, with the transport and the volume; and,
on a player with a screen, Home, Now playing, Lyrics and the D-pad. In YAML:

```yaml
type: custom:gexis-player-card
entity: media_player.living_room   # the player shown first; without it, the first by name
form: full                         # or compact: the D-pad behind a button
look: player                       # or home-assistant: the dashboard's theme
```

It lays itself out by its own width: under about 580 px the screen's
controls sit under what plays, wider beside it. After an update of the
integration, reload the dashboard page once.

## Good to know

- The player changes nothing in Home Assistant. Its API is open to the home
  network with no login, as the player's own settings are.
- With Home Assistant's own *Lyrion Music Server* integration set up too, a
  player also shows there, as Lyrion's player. This integration covers every
  source and the screen.

## Licence

GPL-3.0-or-later, as Gexis Player. The card's fonts, Nunito Sans and IBM Plex
Mono, are under the SIL Open Font License, with their texts beside them in
`custom_components/gexis/frontend/fonts`.
