# Popup modernization — pattern + door/window popups

**Date:** 2026-07-22
**Scope:** First step of a larger effort to modernize the content of every Bubble Card pop-up on the `/lovelace-bubble/overzicht` dashboard. This spec establishes a reusable **state-card grid** pattern and applies it to the two simplest popups: garden doors (`#deuren-tuin`) and upstairs doors/windows (`#ramen-boven`).

## Goal

Replace the plain `custom:auto-entities` → `entities` lists with a glanceable, polished layout that shows, per sensor, **open/closed state + how long it has been in that state**. Look should be "fancy but not too neon" — calm translucent state tints, no glow.

## Reusable pattern: "state-card grid"

A vertical stack inside the pop-up's `cards:`:

1. **Summary strip** — one full-width row showing an at-a-glance count, tinted by whether anything is "active" (open). Driven by an existing group sensor where available.
2. **Section label** — small uppercase muted label per area (omit if a popup has a single group).
3. **State-card grid** — `type: grid, columns: 2, square: false` of state cards.

### State card (per entity)

- A `custom:bubble-card`, `card_type: button`, `button_type: name`.
- **Icon** swaps by state automatically: **omit `icon:`** so the card uses the entity's device_class default, which HA already toggles open↔closed (door → `mdi:door`/`mdi:door-open`; window → closed/open variants). Only set `icon:` explicitly if a default looks wrong.
- **Name** = short friendly label (room/position; the section already gives area context).
- **Subtitle** (custom, via `.bubble-state::after`) = `‹state word› · ‹duration›`:
  - state word: `open` / `dicht` (Dutch).
  - duration: compact Dutch relative time since `last_changed`: `net` (<1 min), `N min`, `N uur`, `1 dag`, `N dagen`. Computed in JS from `hass.states[id].last_changed`.
- **Background tint** (translucent, no glow): closed → soft green `rgba(45,170,115,0.13)`; open → soft amber `rgba(238,160,55,0.16)`. Icon tile a touch stronger (`0.20`/`0.22`).
- **tap_action / hold** → `more-info` on the entity (free history + battery; these sensors are read-only).
- `modules: [bubble_neon_icon_only]` is **not** used here (we want calm tints, not per-icon neon).

### Summary strip

- A `custom:bubble-card`, `button_type: name`, entity = the area group sensor.
- Name rendered via `.bubble-state::after` = `"‹N› open · ‹M› dicht"` (or `"Alles dicht"` when none open), computed from the group's member `entity_id` list in JS.
- Tint: amber if group state is `on` (something open), else green.
- No tap action (informational) — or tap → more-info of the group. Default: no action.

## Popup specs

### `#deuren-tuin` — bpp_doors_garden.yaml

- Keep `width_desktop: 680px`, `popup_mode: centered`, `full_width_on_mobile: true`, name "Deuren in de tuin", icon `mdi:door-sliding`.
- Summary strip driven by `binary_sensor.doors_and_windows_garden`.
- One section **"Schuurdeuren"**, grid of 2 door cards:
  - `binary_sensor.sheddoor_openclose_contact` → "Schuurdeur"
  - `binary_sensor.cabindoor_openclose_contact` → "Blokhutdeur"

### `#ramen-boven` — bpp_doors_upstairs.yaml

- Keep `width_desktop: 760px`, `popup_mode: centered`, `full_width_on_mobile: true`, name "Deuren en ramen boven", icon `mdi:window-closed-variant`.
- Summary strip driven by `binary_sensor.doors_and_windows_upstairs`.
- Section **"Master bedroom"**, grid of 2:
  - `binary_sensor.window_masterbed_1_openclose_contact` → "Raam 1"
  - `binary_sensor.window_masterbed_2_openclose_contact` → "Raam 2"
- Section **"Overig"**, grid of 3:
  - `binary_sensor.window_eva_openclose_contact` → "Eva"
  - `binary_sensor.window_noaroom_openclose_contact` → "Noa"
  - `binary_sensor.window_guestroom_openclose_contact` → "Logeerkamer"

## Implementation notes (Bubble Card)

- Section labels: a lightweight full-width element — a `custom:bubble-card` `card_type: separator` with the label as its name is the native option (styled small/uppercase via `styles`). Acceptable alternative: a `markdown` card. Prefer the separator for consistency.
- 2-column grid: wrap each section's cards in `type: grid, columns: 2, square: false` so the pop-up's vertical `cards:` list gets side-by-side cards.
- Tint + subtitle live in each card's `styles:` block using `${…}` JS templating (`hass`, `state` available). Reuse one duration helper expression across cards (copy per card — Bubble has no shared-macro mechanism).
- Duration helper (reference):
  ```
  const d = (iso) => { if(!iso) return ''; const s=(Date.now()-new Date(iso))/1000;
    if(s<60) return 'net'; const m=s/60; if(m<60) return Math.round(m)+' min';
    const h=m/60; if(h<24) return Math.round(h)+' uur';
    const day=Math.round(h/24); return day+(day===1?' dag':' dagen'); };
  ```
- Verify live in the controlled browser tab (open each hash, check tint by state, subtitle text, more-info on tap).

## Out of scope

- The other ~30 popups (energy, climate, lights, people, media, etc.) — they adopt this pattern in later specs/steps.
- Battery/health surfacing beyond what more-info already provides.
- Any control affordances (these entities are read-only).
- Changing widths, modes, or the tile subtitles on the dashboard itself.

## Success criteria

- Both popups render the summary strip + tinted 2-column state cards, no error cards.
- Subtitle shows correct state word + a sensible Dutch duration.
- Open sensors are amber, closed are green; tapping a card opens its more-info.
- Pattern is documented well enough to reuse for the next popup without re-deciding the visual language.
