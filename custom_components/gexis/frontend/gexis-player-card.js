/* Gexis Player card for Home Assistant dashboards (ADR-0163): every Gexis
 * player in the home, what it plays, its transport and volume, and on a
 * player with a screen the quick actions and the D-pad. One file, no build,
 * no dependency; drawn from design/source/19 (HA Card.dc.html), the player's
 * look by default. Everything goes through Home Assistant's own services. */

const VERSION = '0.3.0';
const FONTS = new URL('fonts/', import.meta.url).href;

/* media_player supported_features */
const F = {
  PAUSE: 1, VOLUME_SET: 4, VOLUME_MUTE: 8, PREVIOUS_TRACK: 16, NEXT_TRACK: 32,
  PLAY: 16384, SHUFFLE_SET: 32768, REPEAT_SET: 262144,
};

const SOURCES = {
  lyrion: { name: 'Lyrion', ink: 'var(--gx-src-lyrion)' },
  spotify: { name: 'Spotify', ink: 'var(--gx-src-spotify)' },
  bluetooth: { name: 'Bluetooth', ink: 'var(--gx-src-bluetooth)' },
  plexamp: { name: 'Plexamp', ink: 'var(--gx-src-plexamp)' },
  other: { name: '', ink: 'var(--gx-ink-2)' },
};

const KEY_NAMES = { up: 'Up', down: 'Down', left: 'Left', right: 'Right', ok: 'OK', back: 'Back' };
const SENT_MS = 1200;

/* The Spotify mark at 80 px, and the Gexis mark (design/source/19). */
const SPOTIFY = 'data:image/png;base64,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';
const MARK = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjMwLjE3IDMwLjE3IDkwLjUxIDkwLjUxIiByb2xlPSJpbWciIGFyaWEtbGFiZWw9ImdleGlzIHNvdW5kIj48ZyB0cmFuc2Zvcm09InRyYW5zbGF0ZSgzMC4xNywzMC4xNykiPjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKDQ1LjI2LDQ1LjI2KSByb3RhdGUoNDUpIj48cmVjdCB4PSItMzIiIHk9Ii0zMiIgd2lkdGg9IjI4LjY0IiBoZWlnaHQ9IjI4LjY0IiByeD0iNy41OSIgZmlsbD0iIzJjNDA0ZiI+PC9yZWN0PjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKC0xNy42OCwtMTcuNjgpIHJvdGF0ZSgtNDUpIj48cGF0aCBkPSJNLTAuNDMgNy44MlEtMS43NiA3LjgyIC0yLjYyIDcuNjFRLTMuNDcgNy40IC0zLjg3IDdRLTQuMjcgNi42IC00LjI3IDYuMDFRLTQuMjcgNS4zMiAtMy43MiA0Ljg4US0zLjE3IDQuNDQgLTIuMDkgNC4zOFY0LjA3US0yLjkyIDQuMDcgLTMuMzcgMy45US0zLjgyIDMuNzMgLTMuODIgMy4yN1EtMy44MiAyLjg0IC0zLjM4IDIuNDlRLTIuOTQgMi4xNSAtMS45MSAxLjk2VjEuNjVRLTIuODUgMS41NiAtMy4zOSAxLjAzUS0zLjk0IDAuNDkgLTMuOTQgLTAuNFEtMy45NCAtMS4xNCAtMy41MSAtMS43NVEtMy4wOSAtMi4zNyAtMi4yNCAtMi43NFEtMS4zOCAtMy4xMSAtMC4xMSAtMy4xMUg0LjA0Vi0xLjI3TDEuNSAtMS42Vi0xLjI1UTIuNDkgLTEuMTEgMi45MiAtMC43OVEzLjM1IC0wLjQ3IDMuMzUgMC4xMVEzLjM1IDAuNzEgMi45MyAxLjE4UTIuNTIgMS42NSAxLjc2IDEuOTJRMSAyLjE4IC0wLjA1IDIuMThRLTAuMjMgMi4xOCAtMC40NiAyLjE3US0wLjY4IDIuMTUgLTEuMjYgMi4wOVEtMS41MSAyLjMgLTEuNjQgMi40NFEtMS43OCAyLjU5IC0xLjc4IDIuNzFRLTEuNzggMi44IC0xLjcgMi44NlEtMS42MyAyLjkyIC0xLjQ5IDIuOTVRLTEuMzQgMi45OCAtMS4xOCAyLjk4SDEuMjdRMS41NyAyLjk4IDIuMDYgMy4wMVEyLjU2IDMuMDUgMy4wNSAzLjI1UTMuNTQgMy40NSAzLjg4IDMuODlRNC4yMiA0LjMzIDQuMjIgNS4xNVE0LjIyIDYuMDQgMy43MiA2LjY0UTMuMjIgNy4yNCAyLjE5IDcuNTNRMS4xNiA3LjgyIC0wLjQzIDcuODJaTS0wLjEyIDUuODZRMC43NiA1Ljg2IDEuMjUgNS43N1ExLjc0IDUuNjggMS45MiA1LjQ5UTIuMTEgNS4zIDIuMTEgNVEyLjExIDQuNzMgMi4wMSA0LjU3UTEuOSA0LjQxIDEuNzMgNC4zNVExLjU2IDQuMjkgMS4zOSA0LjI3UTEuMjEgNC4yNiAxLjA5IDQuMjZILTAuODdRLTEuNDMgNC4yNyAtMS42OSA0LjUzUS0xLjk1IDQuNzkgLTEuOTUgNS4xNVEtMS45NSA1LjQzIC0xLjc3IDUuNTlRLTEuNTggNS43NSAtMS4xOCA1LjhRLTAuNzggNS44NiAtMC4xMiA1Ljg2Wk0tMC4yMSAwLjk2UTAuNDMgMC45NiAwLjc2IDAuNjJRMS4wOCAwLjI3IDEuMDggLTAuMjZRMS4wOCAtMC44NCAwLjc1IC0xLjIxUTAuNDIgLTEuNTggLTAuMiAtMS41OFEtMC44MyAtMS41OCAtMS4xOCAtMS4yMVEtMS41MiAtMC44NCAtMS41MiAtMC4yNlEtMS41MiAwLjA5IC0xLjM3IDAuMzdRLTEuMjIgMC42NSAtMC45MyAwLjgxUS0wLjYzIDAuOTYgLTAuMjEgMC45NloiIGZpbGw9IiM3NjkwYTAiPjwvcGF0aD48L2c+PHJlY3QgeD0iMy4zNyIgeT0iLTMyIiB3aWR0aD0iMjguNjQiIGhlaWdodD0iMjguNjQiIHJ4PSI3LjU5IiBmaWxsPSIjMmM0MDRmIj48L3JlY3Q+PGcgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTcuNjgsLTE3LjY4KSByb3RhdGUoLTQ1KSI+PHBhdGggZD0iTTAuMyA1LjIyUS0wLjcgNS4yMiAtMS40OSA0Ljk1US0yLjI4IDQuNjkgLTIuODMgNC4xN1EtMy4zOCAzLjY1IC0zLjY3IDIuODlRLTMuOTcgMi4xMyAtMy45NyAxLjE1US0zLjk3IDAuMiAtMy42OSAtMC42US0zLjQxIC0xLjQxIC0yLjg4IC0xLjk5US0yLjM1IC0yLjU4IC0xLjU5IC0yLjlRLTAuODIgLTMuMjIgMC4xNCAtMy4yMlExLjEgLTMuMjIgMS44MyAtMi45UTIuNTcgLTIuNTkgMy4wNSAtMS45OFEzLjU0IC0xLjM4IDMuNzYgLTAuNVEzLjk4IDAuMzcgMy45IDEuNDhMLTIuMzYgMS41M1YwLjI1TDIuNSAwLjIxTDEuNjUgMC44MVExLjc1IDAuMDUgMS41NiAtMC40M1ExLjM2IC0wLjkxIDAuOTkgLTEuMTNRMC42MSAtMS4zNSAwLjE3IC0xLjM1US0wLjM3IC0xLjM1IC0wLjc3IC0xLjA2US0xLjE4IC0wLjc3IC0xLjQgLTAuMjNRLTEuNjMgMC4zMiAtMS42MyAxLjExUS0xLjYzIDIuMzUgLTEuMDkgMi45MVEtMC41NSAzLjQ3IDAuMjkgMy40N1EwLjcgMy40NyAwLjk3IDMuMzZRMS4yNCAzLjI1IDEuNDEgMy4wN1ExLjU5IDIuOSAxLjY5IDIuNjhRMS43OCAyLjQ3IDEuODQgMi4yN0wzLjk3IDIuNzNRMy44NiAzLjI4IDMuNTkgMy43NFEzLjMyIDQuMiAyLjg3IDQuNTNRMi40MyA0Ljg2IDEuNzkgNS4wNFExLjE2IDUuMjIgMC4zIDUuMjJaIiBmaWxsPSIjNzY5MGEwIj48L3BhdGg+PC9nPjxyZWN0IHg9Ii0zMiIgeT0iMy4zNyIgd2lkdGg9IjI4LjY0IiBoZWlnaHQ9IjI4LjY0IiByeD0iNy41OSIgZmlsbD0iIzJjNDA0ZiI+PC9yZWN0PjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKC0xNy42OCwxNy42OCkgcm90YXRlKC00NSkiPjxwYXRoIGQ9Ik0tMS4yMiA1LjAxVi0zSDEuMjJWNS4wMVpNMC4wMSAtNC4xMlEtMC42OSAtNC4xMiAtMS4wNiAtNC40MlEtMS40NCAtNC43MSAtMS40NCAtNS4yN1EtMS40NCAtNS44NCAtMS4wNiAtNi4xM1EtMC42OSAtNi40MyAwLjAxIC02LjQzUTAuNzIgLTYuNDMgMS4wOSAtNi4xM1ExLjQ2IC01Ljg0IDEuNDYgLTUuMjdRMS40NiAtNC43MSAxLjA5IC00LjQyUTAuNzIgLTQuMTIgMC4wMSAtNC4xMloiIGZpbGw9IiM3NjkwYTAiPjwvcGF0aD48L2c+PHJlY3QgeD0iMy4zNyIgeT0iMy4zNyIgd2lkdGg9IjI4LjY0IiBoZWlnaHQ9IjI4LjY0IiByeD0iNy41OSIgZmlsbD0iI2YyYTQ4ZiI+PC9yZWN0PjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKDE3LjY4LDE3LjY4KSByb3RhdGUoLTQ1KSI+PHBhdGggZD0iTTAuMDUgNS4yMlEtMC43NiA1LjIyIC0xLjQxIDUuMDhRLTIuMDcgNC45MyAtMi41NSA0LjY2US0zLjA0IDQuMzggLTMuMzUgMy45OVEtMy42NiAzLjYgLTMuNzcgMy4xMkwtMS45NCAyLjMzUS0xLjg0IDIuNTkgLTEuNTcgMi44NlEtMS4zMSAzLjEzIC0wLjg3IDMuMjlRLTAuNDIgMy40NiAwLjIxIDMuNDZRMC44MyAzLjQ2IDEuMTcgMy4yOVExLjUxIDMuMTEgMS41MSAyLjc4UTEuNTEgMi41NCAxLjMyIDIuMzlRMS4xMiAyLjI1IDAuNzQgMi4xNFEwLjM3IDIuMDIgLTAuMiAxLjkxUS0wLjc3IDEuNzkgLTEuMzYgMS42M1EtMS45NSAxLjQ3IC0yLjQ3IDEuMTlRLTIuOTggMC45MSAtMy4yOSAwLjQ1US0zLjYxIC0wLjAxIC0zLjYxIC0wLjcyUS0zLjYxIC0xLjQ3IC0zLjIxIC0yLjAzUS0yLjgyIC0yLjU4IC0yLjA0IC0yLjlRLTEuMjUgLTMuMjIgLTAuMTMgLTMuMjJRMC44NyAtMy4yMiAxLjYzIC0yLjk2UTIuMzkgLTIuNyAyLjg5IC0yLjIyUTMuNCAtMS43NCAzLjYgLTEuMDZMMS42NCAtMC4zOFExLjU3IC0wLjcxIDEuMzMgLTAuOTVRMS4xIC0xLjIgMC43NCAtMS4zM1EwLjM3IC0xLjQ2IC0wLjExIC0xLjQ2US0wLjcgLTEuNDYgLTEuMDIgLTEuMjdRLTEuMzUgLTEuMDkgLTEuMzUgLTAuNzlRLTEuMzUgLTAuNTUgLTEuMTMgLTAuMzlRLTAuOTEgLTAuMjMgLTAuNSAtMC4xMlEtMC4wOSAtMC4wMSAwLjQ3IDAuMTFRMS4wNyAwLjIzIDEuNjYgMC4zOVEyLjI0IDAuNTUgMi43MiAwLjgxUTMuMiAxLjA4IDMuNDggMS41MVEzLjc2IDEuOTUgMy43NiAyLjYzUTMuNzYgMy40MyAzLjMzIDQuMDJRMi45IDQuNiAyLjA3IDQuOTFRMS4yNCA1LjIyIDAuMDUgNS4yMloiIGZpbGw9IiMzZDE1MDkiPjwvcGF0aD48L2c+PC9nPjwvZz48L3N2Zz4=';

const P = {
  chevron: 'M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z',
  alert: 'M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z',
  note: 'M12 3V13.55C11.41 13.21 10.73 13 10 13C7.79 13 6 14.79 6 17S7.79 21 10 21 14 19.21 14 17V7H18V3H12Z',
  shuffle: 'M17,3L22.25,7.5L17,12L22.25,16.5L17,21V18H14.26L11.44,15.18L13.56,13.06L15.5,15H17V12L17,9H15.5L6.5,18H2V15H5.26L14.26,6H17V3M2,6H6.5L9.32,8.82L7.2,10.94L5.26,9H2V6Z',
  prev: 'M6,18V6H8V18H6M9.5,12L18,6V18L9.5,12Z',
  pause: 'M14,19H18V5H14M6,19H10V5H6V19Z',
  play: 'M8,5.14V19.14L19,12.14L8,5.14Z',
  next: 'M16,18H18V6H16M6,18L14.5,12L6,6V18Z',
  repeat: 'M17,17H7V14L3,18L7,22V19H19V13H17M7,7H17V10L21,6L17,2V5H5V11H7V7Z',
  repeatOnce: 'M13,15V9H12L10,10V11H11.5V15M17,17H7V14L3,18L7,22V19H19V13H17M7,7H17V10L21,6L17,2V5H5V11H7V7Z',
  volume: 'M14,3.23V5.29C16.89,6.15 19,8.83 19,12C19,15.17 16.89,17.84 14,18.7V20.77C18,19.86 21,16.28 21,12C21,7.72 18,4.14 14,3.23M16.5,12C16.5,10.23 15.5,8.71 14,7.97V16C15.5,15.29 16.5,13.76 16.5,12M3,9V15H7L12,20V4L7,9H3Z',
  muted: 'M12,4L9.91,6.09L12,8.18M4.27,3L3,4.27L7.73,9H3V15H7L12,20V13.27L16.25,17.53C15.58,18.04 14.83,18.46 14,18.7V20.77C15.38,20.45 16.63,19.82 17.68,18.96L19.73,21L21,19.73L12,10.73M19,12C19,12.94 18.8,13.82 18.46,14.64L19.97,16.15C20.62,14.91 21,13.5 21,12C21,7.72 18,4.14 14,3.23V5.29C16.89,6.15 19,8.83 19,12M16.5,12C16.5,10.23 15.5,8.71 14,7.97V10.18L16.45,12.63C16.5,12.43 16.5,12.21 16.5,12Z',
  lock: 'M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z',
  home: 'M12 5.69L17 10.19V18H15V12H9V18H7V10.19L12 5.69M12 3L2 12H5V20H11V14H13V20H19V12H22',
  lyrics: 'M4 5h16v2H4zM4 10h16v2H4zM4 15h10v2H4z',
  back: 'M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z',
  up: 'M7.41,15.41L12,10.83L16.59,15.41L18,14L12,8L6,14L7.41,15.41Z',
  down: 'M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z',
  left: 'M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z',
  right: 'M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z',
  cross: 'M9 2h6v7h7v6h-7v7H9v-7H2V9h7V2zm2 2v7H4v2h7v7h2v-7h7v-2h-7V4h-2z',
  check: 'M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z',
};

const svg = (d, size, extra = '') =>
  `<svg viewBox="0 0 24 24" width="${size}" height="${size}" ${extra} aria-hidden="true"><path d="${d}" fill="currentColor"></path></svg>`;

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const mmss = (s) => {
  s = Math.max(0, Math.floor(s));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = String(s % 60).padStart(2, '0');
  return h ? `${h}:${String(m).padStart(2, '0')}:${r}` : `${m}:${r}`;
};

/* A source's kind from the name the player gives it. */
function sourceKind(name) {
  const s = String(name || '').toLowerCase();
  if (!s) return null;
  if (s.includes('lyrion') || s.includes('squeeze') || s === 'lms') return 'lyrion';
  if (s.includes('spotify')) return 'spotify';
  if (s.includes('bluetooth')) return 'bluetooth';
  if (s.includes('plex')) return 'plexamp';
  return 'other';
}

/* A source's mark, at the state line's size (14) or the artwork well's. */
function sourceMark(kind, size) {
  const k = size >= 30 ? 'well' : size >= 24 ? 'mid' : 'line';
  if (kind === 'lyrion') {
    const [w, g, hs] = k === 'well' ? [5, 4, [18, 36, 26, 32]] : k === 'mid' ? [3, 2, [11, 22, 16, 19]] : [2, 2, [7, 14, 10, 12]];
    return `<span class="bars" style="gap:${g}px;height:${Math.max(...hs)}px">${hs.map((h) => `<span style="width:${w}px;height:${h}px;border-radius:${Math.ceil(w / 2)}px"></span>`).join('')}</span>`;
  }
  if (kind === 'spotify') return `<img src="${SPOTIFY}" alt="" width="${size}" height="${size}" style="display:block">`;
  if (kind === 'bluetooth') {
    return `<svg viewBox="0 0 64 64" width="${size}" height="${size}" style="display:block" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"><rect x="10" y="8" width="22" height="48" rx="5"></rect><line x1="18" y1="49" x2="24" y2="49"></line><path d="M41 24.5a10 10 0 0 1 0 15"></path><path d="M48 17.5a20 20 0 0 1 0 29"></path></g></svg>`;
  }
  if (kind === 'plexamp') {
    const [d, b, f] = k === 'well' ? [38, 3, 19] : k === 'mid' ? [24, 2, 12] : [14, 1.5, 8];
    return `<span class="plex" style="width:${d}px;height:${d}px;border-width:${b}px;font-size:${f}px">P</span>`;
  }
  return '';
}

/* ---- What Home Assistant holds ------------------------------------------ */

function playerIds(hass) {
  const ids = Object.values(hass.entities || {})
    .filter((e) => e.platform === 'gexis' && e.entity_id.startsWith('media_player.') && hass.states[e.entity_id])
    .map((e) => e.entity_id);
  return ids.sort((a, b) => playerName(hass, a).localeCompare(playerName(hass, b)));
}

function playerName(hass, id) {
  const st = hass.states[id];
  const dev = hass.devices?.[hass.entities?.[id]?.device_id];
  return st?.attributes?.friendly_name || dev?.name_by_user || dev?.name || id;
}

/* A player's buttons and remote, found through its device (ADR-0163 D4). */
function siblings(hass, id) {
  const device = hass.entities?.[id]?.device_id;
  const out = { buttons: {}, remote: null };
  if (!device) return out;
  for (const e of Object.values(hass.entities)) {
    if (e.device_id !== device || e.platform !== 'gexis' || !hass.states[e.entity_id]) continue;
    if (e.entity_id.startsWith('button.') && ['home', 'now', 'lyrics'].includes(e.translation_key)) out.buttons[e.translation_key] = e.entity_id;
    else if (e.entity_id.startsWith('remote.')) out.remote = e.entity_id;
  }
  return out;
}

function stateLine(st) {
  if (!st || st.state === 'unavailable' || st.state === 'unknown') return 'Unavailable';
  if (st.state === 'playing' || st.state === 'paused') {
    const kind = sourceKind(st.attributes.source);
    const name = kind && kind !== 'other' ? SOURCES[kind].name : st.attributes.source;
    return (st.state === 'paused' ? 'Paused' : 'Playing') + (name ? ` · ${name}` : '');
  }
  return 'Idle';
}

/* ---- The card ------------------------------------------------------------- */

const STYLE = `
:host { display: block; }
:host(.look-player) {
  --gexis-card-background: #16232c;
  --gexis-card-ink: #e9eef2;
  --gexis-card-ink-2: rgba(233,238,242,0.72);
  --gexis-card-line: rgba(233,238,242,0.10);
  --gexis-card-border: rgba(126,214,188,0.22);
  --gexis-card-radius: 24px;
  --gexis-card-shadow: none;
  --gexis-card-font: 'Nunito Sans','Avenir Next','Segoe UI',system-ui,sans-serif;
  --gexis-card-label-font: 'IBM Plex Mono','Courier New',monospace;
  --gexis-card-label-case: uppercase;
  --gexis-card-label-track: 0.2em;
  --gexis-card-label-size: 12px;
  --gexis-card-play: #f2a48f;
  --gexis-card-on-play: #0d151c;
  --gexis-card-accent: #7ed6bc;
  --gexis-card-volume: #7ed6bc;
  --gexis-card-volume-track: rgba(233,238,242,0.12);
  --gexis-card-fill: rgba(233,238,242,0.07);
  --gexis-card-fill-strong: rgba(233,238,242,0.18);
  --gexis-card-menu: #16232c;
  --gexis-card-menu-shadow: 0 18px 48px rgba(0,0,0,0.5);
  --gexis-card-bleed: 0.55;
  --gexis-card-bleed-scrim: radial-gradient(130% 105% at 20% 42%,rgba(22,36,46,0.3),rgba(14,23,30,0.86));
  --gexis-source-lyrion: #7ed6bc;
  --gexis-source-spotify: #8fd9a8;
  --gexis-source-bluetooth: #9fb4e8;
  --gexis-source-plexamp: rgba(233,238,242,0.8);
}
.root {
  --gx-bg: var(--gexis-card-background,var(--ha-card-background,var(--card-background-color,#fff)));
  --gx-ink: var(--gexis-card-ink,var(--primary-text-color,#212121));
  --gx-ink-2: var(--gexis-card-ink-2,var(--secondary-text-color,#727272));
  --gx-line: var(--gexis-card-line,var(--divider-color,rgba(0,0,0,0.12)));
  --gx-border: var(--gexis-card-border,var(--ha-card-border-color,var(--divider-color,#e0e0e0)));
  --gx-radius: var(--gexis-card-radius,var(--ha-card-border-radius,12px));
  --gx-card-shadow: var(--gexis-card-shadow,var(--ha-card-box-shadow,none));
  --gx-font: var(--gexis-card-font,var(--ha-font-family-body,Roboto,Noto,sans-serif));
  --gx-label-font: var(--gexis-card-label-font,var(--ha-font-family-body,Roboto,Noto,sans-serif));
  --gx-label-case: var(--gexis-card-label-case,none);
  --gx-label-track: var(--gexis-card-label-track,0.01em);
  --gx-label-size: var(--gexis-card-label-size,14px);
  --gx-play: var(--gexis-card-play,var(--primary-color,#009ac7));
  --gx-on-play: var(--gexis-card-on-play,var(--text-primary-color,#fff));
  --gx-accent: var(--gexis-card-accent,var(--primary-color,#009ac7));
  --gx-vol: var(--gexis-card-volume,var(--primary-color,#009ac7));
  --gx-vol-track: var(--gexis-card-volume-track,color-mix(in srgb,var(--primary-color,#009ac7) 20%,transparent));
  --gx-fill: var(--gexis-card-fill,rgba(127,127,127,0.12));
  --gx-fill-2: var(--gexis-card-fill-strong,rgba(127,127,127,0.24));
  --gx-menu: var(--gexis-card-menu,var(--card-background-color,#fff));
  --gx-menu-shadow: var(--gexis-card-menu-shadow,0 6px 24px rgba(0,0,0,0.18));
  --gx-bleed: var(--gexis-card-bleed,0);
  --gx-bleed-scrim: var(--gexis-card-bleed-scrim,none);
  --gx-src-lyrion: var(--gexis-source-lyrion,oklch(0.52 0.09 170));
  --gx-src-spotify: var(--gexis-source-spotify,oklch(0.52 0.12 150));
  --gx-src-bluetooth: var(--gexis-source-bluetooth,oklch(0.5 0.12 272));
  --gx-src-plexamp: var(--gexis-source-plexamp,var(--secondary-text-color,#727272));
  container-type: inline-size;
  position: relative; box-sizing: border-box; width: 100%;
  background: var(--gx-bg); color: var(--gx-ink);
  border: 1px solid var(--gx-border); border-radius: var(--gx-radius); box-shadow: var(--gx-card-shadow);
  font-family: var(--gx-font); font-size: 14px; line-height: 1.4;
  overflow: hidden; -webkit-font-smoothing: antialiased;
}
button {
  all: unset; box-sizing: border-box; cursor: pointer;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  -webkit-tap-highlight-color: transparent;
}
button:focus-visible, .vol:focus-visible { outline: 2px solid var(--gx-accent); outline-offset: 2px; }
button[disabled] { cursor: default; }
@media (hover: hover) {
  .hov:not([disabled]):hover { background: var(--gx-fill); }
  .tile:not([disabled]):hover, .pill:hover, .dpad-btn:hover { background: var(--gx-fill-2); }
}
.press:active { transform: scale(0.95); }
.dir:active { background: var(--gx-fill-2); }
.ellip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.bleed { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
.bleed img { position: absolute; left: -15%; top: -15%; width: 32.5%; height: 32.5%; object-fit: cover;
  filter: blur(11px) saturate(1.3); transform: scale(4); transform-origin: 0 0; opacity: var(--gx-bleed); }
.scrim { position: absolute; inset: 0; background: var(--gx-bleed-scrim); pointer-events: none; }

.switcher { position: relative; display: flex; align-items: center; gap: 12px; padding: 10px 12px 2px 12px; min-height: 52px; }
.sw-btn { justify-content: flex-start; gap: 12px; min-width: 0; flex: 1 1 auto; width: 100%; border-radius: 12px; padding: 4px 8px 4px 4px; }
.sw-btn[disabled] { cursor: default; }
.sw-btn.open { background: var(--gx-fill); }
.mark { width: 36px; height: 36px; flex-shrink: 0; display: block; }
.sw-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.sw-row { display: flex; align-items: center; gap: 4px; min-width: 0; }
.sw-name { flex: 1 1 auto; min-width: 0; font-size: 16px; font-weight: 500; line-height: 1.3; }
.chev { flex-shrink: 0; color: var(--gx-ink-2); transition: transform 160ms ease; }
.sw-state { display: flex; align-items: center; gap: 6px; min-width: 0; font-size: 13px; color: var(--gx-ink-2); }
.src { display: flex; align-items: center; justify-content: center; width: 14px; height: 14px; flex-shrink: 0; }
.sw-state-text { flex: 1 1 auto; min-width: 0; }
.bars { display: flex; align-items: flex-end; }
.bars > span { background: currentColor; display: block; }
.plex { box-sizing: border-box; border-radius: 50%; border-style: solid; border-color: currentColor; display: flex; align-items: center; justify-content: center; font-weight: 800; line-height: 1; }

.unreachable { position: relative; display: flex; align-items: flex-start; gap: 14px; padding: 14px 20px 22px 20px; }
.unreachable svg { flex-shrink: 0; color: var(--gx-ink-2); margin-top: 1px; }
.unreachable .t { font-size: 16px; font-weight: 500; }
.unreachable .n { color: var(--gx-ink-2); text-wrap: pretty; }

.full { position: relative; display: flex; flex-wrap: wrap; }
.np { flex: 1 1 300px; min-width: 0; display: flex; flex-direction: column; box-shadow: -1px -1px 0 0 var(--gx-line); }
.what { display: flex; gap: 16px; padding: 12px 16px 0; align-items: flex-start; }
.well { position: relative; width: clamp(96px,28cqi,128px); aspect-ratio: 1; flex-shrink: 0; border-radius: 10px; overflow: hidden;
  background: var(--gx-fill); display: flex; align-items: center; justify-content: center; }
.well > img.art { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.well-mark { display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; }
.meta { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; padding-top: 2px; }
.title { font-size: 18px; font-weight: 500; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; overflow-wrap: anywhere; }
.sub { font-size: 14px; color: var(--gx-ink-2); }
.pos { padding: 14px 16px 0; display: flex; flex-direction: column; gap: 6px; }
.bar { position: relative; height: 4px; border-radius: 2px; background: var(--gx-fill-2); overflow: hidden; }
.bar > div { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 2px; }
.times { display: flex; justify-content: space-between; font-size: 12px; color: var(--gx-ink-2); font-variant-numeric: tabular-nums; }
.transport { display: flex; align-items: center; justify-content: center; gap: clamp(6px,3cqi,22px); padding: 6px 16px 2px; }
.t44 { width: 44px; height: 44px; border-radius: 50%; }
.t48 { width: 48px; height: 48px; border-radius: 50%; }
.playbtn { width: 56px; height: 56px; border-radius: 50%; background: var(--gx-play); color: var(--gx-on-play); }
.volume { display: flex; align-items: center; gap: 8px; padding: 8px 16px 14px 10px; }
.vol { position: relative; flex: 1; min-width: 0; height: 40px; border-radius: 12px; background: var(--gx-vol-track); overflow: hidden; cursor: pointer; touch-action: none; }
.vol .fill { position: absolute; left: 0; top: 0; bottom: 0; background: var(--gx-vol); }
.vol .knob { position: absolute; top: 12px; bottom: 12px; width: 4px; border-radius: 2px; background: var(--gx-on-play); }
.voltext { min-width: 44px; text-align: right; font-size: 14px; font-weight: 500; font-variant-numeric: tabular-nums; color: var(--gx-ink-2); }
.fixed { display: flex; align-items: center; gap: 10px; padding: 10px 16px 16px 20px; color: var(--gx-ink-2); font-size: 13px; }
.fixed svg { flex-shrink: 0; }

.screen { flex: 1 1 260px; min-width: 0; display: flex; flex-direction: column; gap: 12px; padding: 14px 16px 18px; box-shadow: -1px -1px 0 0 var(--gx-line); }
.label { font-family: var(--gx-label-font); font-size: var(--gx-label-size); font-weight: 500; letter-spacing: var(--gx-label-track); text-transform: var(--gx-label-case); color: var(--gx-ink-2); }
.quick { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 8px; }
.tile { height: 58px; border-radius: 12px; background: var(--gx-fill); flex-direction: column; gap: 3px; min-width: 0; padding: 0 6px; }
.tile span { font-size: 13px; font-weight: 500; white-space: nowrap; }
.tile[disabled] { opacity: 0.38; }
.dpad { display: grid; grid-template-columns: minmax(0,1fr) auto minmax(0,1fr); align-items: end; gap: 8px; padding-top: 4px; }
.pill { justify-self: start; height: 44px; border-radius: 22px; padding: 0 14px 0 10px; background: var(--gx-fill); gap: 6px; }
.pill span { font-size: 14px; font-weight: 500; white-space: nowrap; }
.pad { position: relative; width: clamp(168px,44cqi,216px); aspect-ratio: 1; border-radius: 50%; background: var(--gx-fill); }
.dir { position: absolute; border-radius: 14px; }
.dir.up { left: 32%; top: 3%; width: 36%; height: 28%; }
.dir.down { left: 32%; bottom: 3%; width: 36%; height: 28%; }
.dir.left { top: 32%; left: 3%; height: 36%; width: 28%; }
.dir.right { top: 32%; right: 3%; height: 36%; width: 28%; }
.ok { position: absolute; left: 33%; top: 33%; width: 34%; height: 34%; border-radius: 50%; background: var(--gx-bg); box-shadow: 0 0 0 1px var(--gx-line);
  font-size: 15px; font-weight: 500; letter-spacing: 0.04em; }
.sent { text-align: center; font-size: 12px; color: var(--gx-ink-2); margin-top: -4px; }

.c-np { position: relative; display: flex; flex-direction: column; }
.c-what { display: flex; align-items: center; gap: 12px; padding: 8px 12px 0 16px; }
.c-well { position: relative; width: 56px; height: 56px; flex-shrink: 0; border-radius: 8px; overflow: hidden; background: var(--gx-fill); display: flex; align-items: center; justify-content: center; }
.c-well > img.art { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.c-meta { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.c-title { font-size: 16px; font-weight: 500; line-height: 1.3; }
.c-transport { display: flex; align-items: center; gap: 2px; flex-shrink: 0; }
.c-play { width: 48px; height: 48px; border-radius: 50%; background: var(--gx-play); color: var(--gx-on-play); }
.c-pos { padding: 10px 16px 0; }
.c-pos .bar { height: 3px; }
.c-volume { display: flex; align-items: center; gap: 8px; padding: 6px 16px 0 10px; }
.c-volume .vol { height: 32px; border-radius: 10px; }
.c-volume .knob { top: 9px; bottom: 9px; }
.c-volume .voltext { min-width: 40px; font-size: 13px; }
.c-fixed { display: flex; align-items: center; gap: 8px; padding: 12px 16px 2px 18px; color: var(--gx-ink-2); font-size: 13px; }
.c-quick { display: flex; align-items: center; gap: 6px; padding: 10px 12px 12px 12px; }
.sq { width: 44px; height: 44px; border-radius: 12px; background: var(--gx-fill); }
.sq[disabled] { opacity: 0.38; }
.dpad-btn { height: 44px; border-radius: 12px; padding: 0 14px 0 10px; background: var(--gx-fill); gap: 8px; }
.dpad-btn.open { background: var(--gx-fill-2); }
.dpad-btn span { font-size: 14px; font-weight: 500; white-space: nowrap; }
.c-dpad { display: grid; grid-template-columns: minmax(0,1fr) auto minmax(0,1fr); align-items: end; gap: 8px; padding: 2px 16px 16px; }
.c-pad { position: relative; width: 160px; height: 160px; border-radius: 50%; background: var(--gx-fill); }
.c-pad .dir { border-radius: 12px; }
.c-sent { text-align: center; font-size: 12px; color: var(--gx-ink-2); margin: -10px 0 0; padding-bottom: 12px; }
.c-end { height: 14px; }

.menu-veil { position: absolute; inset: 0; z-index: 4; }
.menu { position: absolute; z-index: 5; left: 8px; right: 8px; top: 60px; max-width: 420px; background: var(--gx-menu);
  border: 1px solid var(--gx-line); border-radius: 12px; box-shadow: var(--gx-menu-shadow); padding: 6px 0; }
.menu .label { padding: 8px 16px 6px; font-size: 12px; }
.menu button { justify-content: flex-start; width: 100%; gap: 12px; min-height: 56px; padding: 0 16px; }
.menu button.current { background: var(--gx-fill); }
.menu .mark { width: 28px; height: 28px; }
.menu .who { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.menu .who .n { display: block; font-size: 15px; font-weight: 500; }
.menu .who .s { display: block; font-size: 13px; color: var(--gx-ink-2); }
.menu .tick { color: var(--gx-accent); flex-shrink: 0; }
`;

/* The player's look names Nunito Sans and IBM Plex Mono; Home Assistant has
 * neither, so the faces are served beside this file and declared once, in
 * the page (a shadow root cannot declare a font). */
function declareFonts() {
  if (document.getElementById('gexis-card-fonts')) return;
  const style = document.createElement('style');
  style.id = 'gexis-card-fonts';
  style.textContent = `
@font-face{font-family:'Nunito Sans';src:url('${FONTS}NunitoSans-Variable.woff2') format('woff2-variations'),url('${FONTS}NunitoSans-Variable.woff2') format('woff2');font-weight:300 800;font-display:swap;}
@font-face{font-family:'IBM Plex Mono';src:url('${FONTS}IBMPlexMono-Regular.woff2') format('woff2');font-weight:400;font-display:swap;}
@font-face{font-family:'IBM Plex Mono';src:url('${FONTS}IBMPlexMono-SemiBold.woff2') format('woff2');font-weight:500 600;font-display:swap;}`;
  document.head.appendChild(style);
}

class GexisPlayerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = { form: 'full', look: 'player' };
    this._current = null;       // the player shown: from the config, then the switcher
    this._menu = false;
    this._dpadOpen = false;
    this._sent = null;           // { text, until }
    this._drag = null;           // the volume while a finger is on it
    this._html = '';
    this.shadowRoot.addEventListener('click', (e) => this._onClick(e));
    this.shadowRoot.addEventListener('pointerdown', (e) => this._onPointer(e));
    this.shadowRoot.addEventListener('keydown', (e) => this._onKey(e));
  }

  static getConfigForm() {
    return {
      schema: [
        { name: 'entity', selector: { entity: { filter: [{ domain: 'media_player', integration: 'gexis' }] } } },
        { name: 'form', selector: { select: { mode: 'dropdown', options: [
          { value: 'full', label: 'Full' }, { value: 'compact', label: 'Compact' }] } } },
        { name: 'look', selector: { select: { mode: 'dropdown', options: [
          { value: 'player', label: "The player's look" }, { value: 'home-assistant', label: "Home Assistant's look" }] } } },
      ],
      computeLabel: (s) => ({ entity: 'Player shown first', form: 'Form', look: 'Look' })[s.name],
    };
  }

  static getStubConfig(hass) {
    const first = playerIds(hass)[0];
    return first ? { entity: first } : {};
  }

  setConfig(config) {
    if (!config || typeof config !== 'object') throw new Error('Invalid configuration');
    if (config.entity && !String(config.entity).startsWith('media_player.')) throw new Error('entity must be a Gexis media player');
    if (config.form && !['full', 'compact'].includes(config.form)) throw new Error('form is full or compact');
    if (config.look && !['player', 'home-assistant'].includes(config.look)) throw new Error('look is player or home-assistant');
    this._config = { form: 'full', look: 'player', ...config };
    this._current = this._config.entity || null;
    this.classList.toggle('look-player', this._config.look === 'player');
    this._html = '';
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._fonts && this._config.look === 'player') { declareFonts(); this._fonts = true; }
    this._render();
  }

  connectedCallback() {
    this._tick = setInterval(() => this._tickPosition(), 1000);
  }

  disconnectedCallback() {
    clearInterval(this._tick);
    clearTimeout(this._sentTimer);
  }

  getCardSize() {
    return this._config.form === 'compact' ? 4 : 9;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  /* ---- the view, from Home Assistant's state ---- */

  /* The card's own player first, then the others by name: the list keeps its
   * order as the switcher moves between them (the design's). */
  _players() {
    const own = this._config.entity;
    const ids = playerIds(this._hass).filter((id) => id !== own);
    if (own && this._hass.states[own]) ids.unshift(own);
    return ids;
  }

  _view() {
    const hass = this._hass;
    const ids = this._players();
    const id = ids.includes(this._current) ? this._current : ids[0];
    if (!id) return null;
    const st = hass.states[id];
    const a = st.attributes || {};
    const unreachable = st.state === 'unavailable' || st.state === 'unknown';
    const active = st.state === 'playing' || st.state === 'paused';
    const kind = active ? sourceKind(a.source) : null;
    const feat = Number(a.supported_features) || 0;
    const has = (f) => (feat & f) !== 0;
    const sib = siblings(hass, id);
    const btn = (k) => sib.buttons[k] && hass.states[sib.buttons[k]];
    const usable = (k) => !!btn(k) && btn(k).state !== 'unavailable';
    const hasButtons = Object.keys(sib.buttons).length > 0;
    const remote = sib.remote && hass.states[sib.remote];
    const hasDpad = !!remote && remote.state !== 'unavailable';
    const art = active && kind !== 'bluetooth' && a.entity_picture ? a.entity_picture : null;
    const duration = Number(a.media_duration) || 0;
    const hasPos = active && kind !== 'bluetooth' && duration > 0 && a.media_position != null;
    return {
      id, ids, st, a, unreachable, active, kind, art, duration, hasPos,
      name: playerName(hass, id),
      line: stateLine(st),
      title: active ? (a.media_title || (kind && kind !== 'other' ? SOURCES[kind].name : a.source) || 'Playing') : 'Nothing playing',
      artist: active ? a.media_artist || '' : '',
      album: active ? a.media_album_name || '' : '',
      playing: st.state === 'playing',
      prev: active && has(F.PREVIOUS_TRACK),
      next: active && has(F.NEXT_TRACK),
      playPause: active && (has(F.PLAY) || has(F.PAUSE)),
      shuffle: active && has(F.SHUFFLE_SET),
      repeat: active && has(F.REPEAT_SET),
      shuffleOn: !!a.shuffle,
      repeatMode: a.repeat || 'off',
      volume: has(F.VOLUME_SET),
      mute: has(F.VOLUME_MUTE),
      muted: !!a.is_volume_muted,
      level: Math.round((Number(a.volume_level) || 0) * 100),
      screen: hasButtons || hasDpad,
      buttons: hasButtons,
      dpad: hasDpad,
      sib, usable,
    };
  }

  _render() {
    if (!this._hass || this._drag !== null) return;
    const v = this._view();
    const html = v ? this._markup(v) : '<div class="root"><div class="unreachable"><div><div class="t">No Gexis player</div><div class="n">Add a player under Settings → Devices &amp; services.</div></div></div></div>';
    if (html === this._html) { this._tickPosition(); return; }
    this._html = html;
    this._v = v;
    this.shadowRoot.innerHTML = `<style>${STYLE}</style>${html}`;
    this._tickPosition();
  }

  /* ---- markup, region by region (data-gexis-card names the design's) ---- */

  _markup(v) {
    const full = this._config.form !== 'compact';
    const multi = v.ids.length > 1;
    const src = v.kind ? SOURCES[v.kind] : null;
    const bleed = this._config.look === 'player' && v.art && !v.unreachable;
    let h = `<div class="root" data-gexis-card="root">`;
    if (bleed) h += `<div class="bleed"><img src="${esc(v.art)}" alt=""></div><div class="scrim"></div>`;
    h += `<div class="switcher" data-gexis-card="switcher">
      <button class="sw-btn${this._menu ? ' open' : ''}" data-act="menu" ${multi ? `aria-haspopup="listbox" aria-expanded="${this._menu}"` : 'disabled'} aria-label="${esc(v.name)}: ${esc(v.line)}">
        <img class="mark" src="${MARK}" alt="" style="opacity:${v.unreachable ? 0.45 : 1}">
        <div class="sw-text">
          <div class="sw-row"><span class="sw-name ellip">${esc(v.name)}</span>${multi ? svg(P.chevron, 22, `class="chev" style="transform:rotate(${this._menu ? 180 : 0}deg)"`) : ''}</div>
          <div class="sw-state">${src && src.name ? `<span class="src" style="color:${src.ink}">${sourceMark(v.kind, 14)}</span>` : ''}<span class="sw-state-text ellip">${esc(v.line)}</span></div>
        </div>
      </button>
    </div>`;
    if (v.unreachable) {
      h += `<div class="unreachable" data-gexis-card="unreachable">${svg(P.alert, 28)}
        <div style="display:flex;flex-direction:column;gap:3px;min-width:0"><div class="t">Can’t reach ${esc(v.name)}</div>
        <div class="n">Home Assistant reconnects when the player is back on the network.</div></div></div>`;
    } else {
      h += full ? this._full(v, src) : this._compact(v, src);
    }
    if (this._menu && multi) h += this._switcherMenu(v);
    return h + '</div>';
  }

  _well(v, src, cls) {
    if (v.art) return `<div class="${cls}"><img class="art" src="${esc(v.art)}" alt=""></div>`;
    const ink = src ? src.ink : 'var(--gx-ink-2)';
    const big = cls === 'well';
    const mark = v.kind && v.kind !== 'other' ? sourceMark(v.kind, big ? 40 : 24) : svg(P.note, big ? 36 : 24);
    return `<div class="${cls}" style="color:${ink}"><span class="${big ? 'well-mark' : ''}" style="display:flex;align-items:center;justify-content:center">${mark}</span></div>`;
  }

  _repeatIcon(v, size) {
    return svg(v.repeatMode === 'one' ? P.repeatOnce : P.repeat, size);
  }

  _full(v, src) {
    const ink = src ? src.ink : 'var(--gx-ink-2)';
    let np = `<div class="what" data-gexis-card="what-plays">${this._well(v, src, 'well')}
      <div class="meta"><div class="title" style="color:${v.active ? 'var(--gx-ink)' : 'var(--gx-ink-2)'}">${esc(v.title)}</div>
      ${v.active ? `${v.artist ? `<div class="sub ellip">${esc(v.artist)}</div>` : ''}${v.album ? `<div class="sub ellip">${esc(v.album)}</div>` : ''}` : ''}</div></div>`;
    if (v.hasPos) {
      np += `<div class="pos" data-gexis-card="position"><div class="bar"><div data-pos-fill style="background:${ink};width:0%"></div></div>
        <div class="times"><span data-pos-text></span><span>${mmss(v.duration)}</span></div></div>`;
    }
    if (v.prev || v.next || v.playPause) {
      np += `<div class="transport" data-gexis-card="transport">
        ${v.shuffle ? `<button class="t44 hov" data-act="shuffle" aria-label="Shuffle" aria-pressed="${v.shuffleOn}" style="color:${v.shuffleOn ? 'var(--gx-accent)' : 'var(--gx-ink-2)'}">${svg(P.shuffle, 22)}</button>` : ''}
        ${v.prev ? `<button class="t48 hov" data-act="prev" aria-label="Previous">${svg(P.prev, 30)}</button>` : ''}
        ${v.playPause ? `<button class="playbtn press" data-act="play" aria-label="${v.playing ? 'Pause' : 'Play'}">${v.playing ? svg(P.pause, 30) : svg(P.play, 32)}</button>` : ''}
        ${v.next ? `<button class="t48 hov" data-act="next" aria-label="Next">${svg(P.next, 30)}</button>` : ''}
        ${v.repeat ? `<button class="t44 hov" data-act="repeat" aria-label="Repeat: ${v.repeatMode}" style="color:${v.repeatMode !== 'off' ? 'var(--gx-accent)' : 'var(--gx-ink-2)'}">${this._repeatIcon(v, 22)}</button>` : ''}
      </div>`;
    }
    np += this._volume(v, false);
    let h = `<div class="full"><div class="np" data-gexis-card="now-playing">${np}</div>`;
    if (v.screen) {
      h += `<div class="screen" data-gexis-card="screen"><div class="label">On the player’s screen</div>
        ${v.buttons ? this._quickTiles(v) : ''}
        ${v.dpad ? `<div class="dpad" data-gexis-card="dpad">${this._back()}${this._pad('pad')}<div></div></div>
        ${this._sentText() ? `<div class="sent" aria-live="polite">${esc(this._sentText())}</div>` : ''}` : ''}
      </div>`;
    }
    return h + '</div>';
  }

  _volume(v, compact) {
    if (!v.volume) {
      return `<div class="${compact ? 'c-fixed' : 'fixed'}" data-gexis-card="volume-fixed">${svg(P.lock, compact ? 16 : 18)}
        <span>${compact ? 'Fixed output · set on the amplifier' : 'Fixed output · the volume is set on the amplifier'}</span></div>`;
    }
    const level = v.level;
    const knob = level > 6 ? (v.muted ? 0.5 : 0.9) : 0;
    return `<div class="${compact ? 'c-volume' : 'volume'}" data-gexis-card="volume">
      ${v.mute ? `<button class="t44 hov" data-act="mute" aria-label="${v.muted ? 'Unmute' : 'Mute'}" style="color:${v.muted ? 'var(--gx-accent)' : 'var(--gx-ink)'}">${svg(v.muted ? P.muted : P.volume, compact ? 22 : 24)}</button>` : '<div style="width:44px;flex-shrink:0"></div>'}
      <div class="vol" data-vol role="slider" tabindex="0" aria-label="Volume" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${level}">
        <div class="fill" style="width:${level}%;opacity:${v.muted ? 0.35 : 1}"></div>
        <div class="knob" style="left:calc(${level}% - ${compact ? 9 : 10}px);opacity:${knob}"></div>
      </div>
      <span class="voltext">${v.muted ? 'Muted' : `${level}%`}</span></div>`;
  }

  _quickTiles(v) {
    const tile = (k, label, icon) =>
      `<button class="tile" data-act="go" data-key="${k}" aria-label="${label}" ${v.usable(k) ? '' : 'disabled'}>${svg(icon, 20)}<span>${label}</span></button>`;
    return `<div class="quick" data-gexis-card="quick-actions">${tile('home', 'Home', P.home)}${tile('now', 'Now playing', P.note)}${tile('lyrics', 'Lyrics', P.lyrics)}</div>`;
  }

  _back() {
    return `<button class="pill press" data-act="key" data-key="back" aria-label="Back">${svg(P.back, 20)}<span>Back</span></button>`;
  }

  _pad(cls) {
    const s = cls === 'pad' ? 30 : 28;
    const dir = (k) => `<button class="dir ${k}" data-act="key" data-key="${k}" aria-label="${KEY_NAMES[k]}">${svg(P[k], s)}</button>`;
    return `<div class="${cls}">${dir('up')}${dir('down')}${dir('left')}${dir('right')}
      <button class="ok press" data-act="key" data-key="ok" aria-label="OK">OK</button></div>`;
  }

  _compact(v, src) {
    const ink = src ? src.ink : 'var(--gx-ink-2)';
    let h = `<div class="c-np" data-gexis-card="now-playing">
      <div class="c-what" data-gexis-card="what-plays">${this._well(v, src, 'c-well')}
        <div class="c-meta"><div class="c-title ellip" style="color:${v.active ? 'var(--gx-ink)' : 'var(--gx-ink-2)'}">${esc(v.title)}</div>
        ${v.active && v.artist ? `<div class="sub ellip">${esc(v.artist)}</div>` : ''}</div>
        ${v.prev || v.next || v.playPause ? `<div class="c-transport" data-gexis-card="transport">
          ${v.prev ? `<button class="t44 hov" data-act="prev" aria-label="Previous">${svg(P.prev, 26)}</button>` : ''}
          ${v.playPause ? `<button class="c-play press" data-act="play" aria-label="${v.playing ? 'Pause' : 'Play'}">${v.playing ? svg(P.pause, 26) : svg(P.play, 28)}</button>` : ''}
          ${v.next ? `<button class="t44 hov" data-act="next" aria-label="Next">${svg(P.next, 26)}</button>` : ''}
        </div>` : ''}
      </div>`;
    if (v.hasPos) h += `<div class="c-pos" data-gexis-card="position"><div class="bar"><div data-pos-fill style="background:${ink};width:0%"></div></div></div>`;
    h += this._volume(v, true);
    if (v.screen) {
      const sq = (k, label, icon) => `<button class="sq" data-act="go" data-key="${k}" aria-label="${label}" ${v.usable(k) ? '' : 'disabled'}>${svg(icon, 22)}</button>`;
      h += `<div class="c-quick" data-gexis-card="quick-actions">
        ${v.buttons ? `${sq('home', 'Home', P.home)}${sq('now', 'Now playing', P.note)}${sq('lyrics', 'Lyrics', P.lyrics)}` : ''}
        <div style="flex:1"></div>
        ${v.dpad ? `<button class="dpad-btn${this._dpadOpen ? ' open' : ''}" data-act="dpad" aria-expanded="${this._dpadOpen}">${svg(P.cross, 22)}<span>D-pad</span>${svg(P.chevron, 18, `style="color:var(--gx-ink-2);transform:rotate(${this._dpadOpen ? 180 : 0}deg);transition:transform 160ms ease"`)}</button>` : ''}
      </div>`;
      if (v.dpad && this._dpadOpen) {
        h += `<div class="c-dpad" data-gexis-card="dpad">${this._back()}${this._pad('c-pad')}<div></div></div>
          ${this._sentText() ? `<div class="c-sent" aria-live="polite">${esc(this._sentText())}</div>` : ''}`;
      }
    } else {
      h += '<div class="c-end"></div>';
    }
    return h + '</div>';
  }

  _switcherMenu(v) {
    const rows = v.ids.map((id) => {
      const st = this._hass.states[id];
      const cur = id === v.id;
      const off = !st || st.state === 'unavailable';
      return `<button role="option" aria-selected="${cur}" class="${cur ? 'current' : ''} hov" data-act="pick" data-id="${esc(id)}">
        <img class="mark" src="${MARK}" alt="" style="opacity:${off ? 0.45 : 1}">
        <div class="who"><span class="n ellip">${esc(playerName(this._hass, id))}</span><span class="s ellip">${esc(stateLine(st))}</span></div>
        ${cur ? svg(P.check, 22, 'class="tick"') : ''}</button>`;
    }).join('');
    return `<div class="menu-veil" data-act="close"></div>
      <div class="menu" data-gexis-card="switcher-menu" role="listbox" aria-label="Gexis players"><div class="label">Gexis players</div>${rows}</div>`;
  }

  /* ---- the position, moved every second without a redraw ---- */

  _position(v) {
    const a = v.a;
    let pos = Number(a.media_position) || 0;
    if (v.playing && a.media_position_updated_at) {
      pos += (Date.now() - new Date(a.media_position_updated_at).getTime()) / 1000;
    }
    return Math.min(Math.max(pos, 0), v.duration || pos);
  }

  _tickPosition() {
    const v = this._v;
    if (!v || !v.hasPos) return;
    const pos = this._position(v);
    const fill = this.shadowRoot.querySelector('[data-pos-fill]');
    if (fill) fill.style.width = `${Math.round((pos / v.duration) * 1000) / 10}%`;
    const text = this.shadowRoot.querySelector('[data-pos-text]');
    if (text) text.textContent = mmss(pos);
  }

  /* ---- what a press does: Home Assistant's services only (ADR-0163 D5) ---- */

  _sentText() {
    return this._sent && this._sent.until > Date.now() ? this._sent.text : '';
  }

  _say(text, ms = SENT_MS) {
    clearTimeout(this._sentTimer);
    this._sent = { text, until: Date.now() + ms };
    this._html = '';
    this._render();
    this._sentTimer = setTimeout(() => { this._sent = null; this._html = ''; this._render(); }, ms);
  }

  _toast(err) {
    this.dispatchEvent(new CustomEvent('hass-notification', {
      detail: { message: err?.message || String(err) }, bubbles: true, composed: true,
    }));
  }

  async _call(domain, service, data) {
    try {
      await this._hass.callService(domain, service, data);
      return true;
    } catch (err) {
      this._toast(err);
      return false;
    }
  }

  _onClick(e) {
    const el = e.target.closest('[data-act]');
    if (!el || el.disabled) return;
    const v = this._v;
    const act = el.dataset.act;
    if (act === 'menu') { this._menu = !this._menu; this._html = ''; this._render(); return; }
    if (act === 'close') { this._menu = false; this._html = ''; this._render(); return; }
    if (act === 'pick') { this._current = el.dataset.id; this._menu = false; this._html = ''; this._render(); return; }
    if (act === 'dpad') { this._dpadOpen = !this._dpadOpen; this._html = ''; this._render(); return; }
    if (!v) return;
    const id = { entity_id: v.id };
    if (act === 'play') this._call('media_player', v.playing ? 'media_pause' : 'media_play', id);
    else if (act === 'prev') this._call('media_player', 'media_previous_track', id);
    else if (act === 'next') this._call('media_player', 'media_next_track', id);
    else if (act === 'shuffle') this._call('media_player', 'shuffle_set', { ...id, shuffle: !v.shuffleOn });
    else if (act === 'repeat') {
      const nextMode = { off: 'all', all: 'one', one: 'off' }[v.repeatMode] || 'off';
      this._call('media_player', 'repeat_set', { ...id, repeat: nextMode });
    } else if (act === 'mute') this._call('media_player', 'volume_mute', { ...id, is_volume_muted: !v.muted });
    else if (act === 'go') {
      const button = v.sib.buttons[el.dataset.key];
      if (button) this._call('button', 'press', { entity_id: button });
    } else if (act === 'key') {
      const key = el.dataset.key;
      if (!v.sib.remote) return;
      this._call('remote', 'send_command', { entity_id: v.sib.remote, command: key }).then((ok) => {
        if (ok) this._say(`Sent ${KEY_NAMES[key]}`);
      });
    }
  }

  _onKey(e) {
    if (e.key === 'Escape' && this._menu) { this._menu = false; this._html = ''; this._render(); return; }
    const vol = e.target.closest && e.target.closest('[data-vol]');
    if (vol && this._v && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
      e.preventDefault();
      const level = Math.max(0, Math.min(100, this._v.level + (e.key === 'ArrowRight' ? 5 : -5)));
      this._call('media_player', 'volume_set', { entity_id: this._v.id, volume_level: level / 100 });
    }
  }

  /* The volume follows the finger and is set when it lifts, so a drag is one
   * change, not fifty; the card is not redrawn meanwhile. */
  _onPointer(e) {
    const bar = e.target.closest('[data-vol]');
    if (!bar || !this._v) return;
    e.preventDefault();
    const fill = bar.querySelector('.fill');
    const knob = bar.querySelector('.knob');
    const text = bar.parentElement.querySelector('.voltext');
    const compact = !!bar.closest('.c-volume');
    const at = (x) => {
      const r = bar.getBoundingClientRect();
      return Math.max(0, Math.min(100, Math.round(((x - r.left) / r.width) * 100)));
    };
    const show = (level) => {
      this._drag = level;
      fill.style.width = `${level}%`;
      fill.style.opacity = 1;
      knob.style.left = `calc(${level}% - ${compact ? 9 : 10}px)`;
      knob.style.opacity = level > 6 ? 0.9 : 0;
      if (text) text.textContent = `${level}%`;
    };
    const id = this._v.id;
    bar.setPointerCapture(e.pointerId);
    show(at(e.clientX));
    const move = (ev) => show(at(ev.clientX));
    const up = () => {
      bar.removeEventListener('pointermove', move);
      bar.removeEventListener('pointerup', up);
      bar.removeEventListener('pointercancel', up);
      const level = this._drag;
      this._drag = null;
      this._html = '';
      this._call('media_player', 'volume_set', { entity_id: id, volume_level: level / 100 });
      this._render();
    };
    bar.addEventListener('pointermove', move);
    bar.addEventListener('pointerup', up);
    bar.addEventListener('pointercancel', up);
  }
}

if (!customElements.get('gexis-player-card')) {
  customElements.define('gexis-player-card', GexisPlayerCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'gexis-player-card',
    name: 'Gexis Player',
    description: 'Every Gexis player: what plays, the transport and volume, and on a player with a screen its quick actions and D-pad.',
    preview: true,
    documentationURL: 'https://github.com/gcarstoiu/gexis-player-homeassistant',
  });
  console.info(`%c GEXIS-PLAYER-CARD %c ${VERSION} `, 'background:#16232c;color:#7ed6bc;font-weight:600', 'background:#7ed6bc;color:#16232c');
}
