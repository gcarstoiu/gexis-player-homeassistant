# Gexis Player for Home Assistant

Each [Gexis Player](https://github.com/gcarstoiu/gexis-player) on the home
network in Home Assistant, as a media player: what plays, with its artwork;
play, pause, next and previous; volume and mute; the source playing; the
equaliser, on or off, and its setting. On a player with a screen, four
switches as well - the screen (display standby), the Home Assistant
dashboard, the visualiser and the idle screen - three buttons (Home, Now
playing and Lyrics), a D-pad, and actions that put a page of Home
Assistant's on the screen for a while - the cameras when the doorbell rings.
And a card for dashboards, for every player in the home.

## What it needs

- Home Assistant 2026.3 or later.
- Gexis Player 1.5.0 or later (the D-pad 1.6.0 or later; the equaliser,
  seeking and mute with Fixed volume 1.7.0 or later; pages 1.15.0 or later).
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
| Media player | Playing, paused or idle; title, artist, album, artwork, position. Play, pause, next and previous when the source playing has them; shuffle and repeat where it has them; seeking where it has it; volume and mute, and with Fixed volume mute alone where the output has a volume control of its own; the source playing (each source is taken over from its own app, as on the player). As on the player, a control the source has stays while it cannot be used (Next on the last track); `available_controls` lists those that work now. |
| Screen | On is lit; off is display standby. |
| Dashboard | Puts the player's Home Assistant dashboard up or takes it down. Unavailable until a dashboard address is set on the player (*Settings → Display → Home Assistant dashboard*). |
| Visualiser | Shows or hides the visualiser. Unavailable when the output cannot feed the meters. |
| Idle screen | Puts the idle screen up or takes it down, as the phone's *Idle* does. Unavailable while the idle screen is switched off on the player. |
| Equaliser | Switches the equaliser on or off, for the output in use. Off, the sound is untouched. |
| Equaliser setting | The setting in use: the presets, then the owner's own (`presets` and `own` list each); *Custom* while bands moved on the player are not saved, never chosen from here. |
| Home | Opens Home on the player's screen. |
| Now playing, Lyrics | Opens Now Playing or the lyrics on the player's screen. Unavailable while no source is active. |
| D-pad | A remote for the player's screen: `remote.send_command` with `up`, `down`, `left`, `right`, `ok`, `back` or `home`, with `num_repeats` and `delay_secs`. On while the screen is lit; turning it off or on is the screen's standby. Needs Gexis Player 1.6.0 or later; an older player is asked to update. |
| Page | On while a page from Home Assistant is on the player's screen (below); `page_id` is its name, `until` when its time ends, `closed_id` and `closed_by` the last one's name and why it went (`touch`, `key`, `limit`, `asked`, `replaced`, `heat`, `off`). Unavailable while *Pages from Home Assistant* is off on the player. |

The switches (the equaliser's apart), buttons, D-pad and Page are unavailable
on a player without a screen.

## A page on the player's screen

Two actions on the player's media player put a page of Home Assistant's on
its screen for a while and take it down - for example a view of the cameras
when the doorbell rings:

```yaml
action: gexis.show_page
target:
  entity_id: media_player.living_room
data:
  url: http://homeassistant.local:8123/home-security/tv   # as the player reaches it
  id: cameras          # a name for it; "page" if left out
  seconds: 120         # 10 to 3600; 600 if left out
```

```yaml
action: gexis.hide_page
target:
  entity_id: media_player.living_room
data:
  id: cameras          # only this page; any if left out
```

The page shows over whatever is on the screen, the music playing on, and a
screen in standby wakes for it. It goes at a touch on the screen or a key on
a remote, at the end of its time, with `gexis.hide_page`, when the player
gets hot, or when a person asks the player for something else; then the
screen is as it was. A second `show_page` with the same `id` starts its time
again.

For a page that has to be there at once - a doorbell does not wait for
Home Assistant to load - the player can keep one page loaded and hidden;
`gexis.show_page` with the same `url` then only reveals it, and every close
hides it again:

```yaml
action: gexis.preload_page
target:
  entity_id: media_player.living_room
data:
  url: http://homeassistant.local:8123/home-security/tv   # empty or left out: none kept
```

The player loads it again after a restart; sending the same `url` again
loads it afresh. A hidden page still reads itself as visible, so it has to
stop its own video while it is not shown - from Home Assistant's own state,
for example *Page* (`preloaded` says whether one is kept). It takes about
60-90 MB of the player's memory.

On the player, *Pages from Home Assistant* has to be on (*Settings →
Display*); until then the action fails and says so, and *Page* is
unavailable. Home Assistant has to allow its pages to be shown inside
another page and let the player in, as for the player's dashboard. Live
video is heavy for the player's Raspberry Pi: show few cameras, in their
smaller streams.

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

It shows one player at a time, with a switcher to the others, laid out as
the player's phone remote: what plays, with previous, play or pause and next
(a control the source cannot use now greyed, as on the player); on a player
with a screen, the D-pad with Home, Lyrics, Back and Meters at its corners,
then Standby, the idle screen, Playing and Room, each left out where the
phone leaves it out; and the volume, with mute and the equaliser's setting,
beside a button that opens the equaliser. A player without a screen gets a
large cover and a bar to move through the track. In YAML:

```yaml
type: custom:gexis-player-card
entity: media_player.living_room   # the player shown first; without it, the first by name
form: full                         # or compact: one row, the D-pad behind a button
look: player                       # or home-assistant: the dashboard's theme
```

The full form is at most 440 px wide, centred in a wider column. After an
update of the integration, reload the dashboard page once.

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
