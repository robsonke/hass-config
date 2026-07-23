# Popup modernization — pattern + door/window popups

**Date:** 2026-07-22
**Scope:** First step of a larger effort to modernize the content of every Bubble Card pop-up on the `/lovelace-bubble/overzicht` dashboard. This spec establishes a reusable **state-card grid** pattern and applies it to the two simplest popups: garden doors (`#deuren-tuin`) and upstairs doors/windows (`#ramen-boven`).

## Goal

Replace the plain `custom:auto-entities` → `entities` lists with a glanceable, polished layout that shows, per sensor, **open/closed state + how long it has been in that state**. Look should be "fancy but not too neon" — calm translucent state tints, no glow.

## Reusable pattern: "state-card grid"

A vertical stack inside the pop-up's `cards:`:

1. **Summary in the pop-up header** — the pop-up card gets `entity: <group sensor>` + `show_state: true`, which makes the header render a state line under the title. Override it via the pop-up's `styles:` (`.bubble-state::after`) to the computed "N open · M dicht" count, and calm the header's default on-state blue (`.bubble-button-background`) to the same soft tint the cards use. (Earlier revision used a separate summary *card*; the header is cleaner and saves vertical space.)
2. **Section label** — small uppercase muted label per area (omit if a popup has a single group).
3. **State-card grid** — `type: grid, columns: 2, square: false` of state cards.

### State card (per entity)

- A `custom:bubble-card`, `card_type: button`, `button_type: name`.
- **Icon** swaps by state automatically: **omit `icon:`** so the card uses the entity's device_class default, which HA already toggles open↔closed (door → `mdi:door`/`mdi:door-open`; window → closed/open variants). Only set `icon:` explicitly if a default looks wrong.
- **Name** = short friendly label (room/position; the section already gives area context).
- **Subtitle** (custom, via `.bubble-state::after`) = `‹state word› · ‹duration›`:
  - state word: `open` / `dicht` (Dutch).
  - duration: compact Dutch relative time since `last_changed`: `net` (<1 min), `N min`, `N uur`, `1 dag`, `N dagen`. Computed in JS from `hass.states[id].last_changed`.
- **Background tint** (translucent, no glow): closed → soft green `rgba(45,170,115,0.13)`; open → soft blue `rgba(55,138,221,0.16)`. Icon tile a touch stronger (`0.20`/`0.22`).
- **tap_action / hold** → `more-info` on the entity (free history + battery; these sensors are read-only).
- `modules: [bubble_neon_icon_only]` is **not** used here (we want calm tints, not per-icon neon).

### Summary (in the header)

- Set `entity: <group sensor>` and `show_state: true` on the pop-up card itself.
- In the pop-up's `styles:`, hide the raw header state (`.bubble-state { font-size: 0 }`) and inject via `.bubble-state::after` = `"‹N› open · ‹M› dicht"` (or `"Alles dicht"` when none open), computed from the group's member `entity_id` list in JS. Colour the text blue when open, green when closed.
- Calm the header's default on-state background: `.bubble-button-background { background-color: <soft blue/green by state> }` (otherwise it renders bright blue when the group is `on`). Optionally tint `.bubble-icon-container` to match.
- These pop-up-level `styles` only reach the header (its own shadow root); the nested state cards have their own `styles`, so `.bubble-state` here never collides with the card subtitles.

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

## Variations (added while doing `#deuren-beneden`)

- **Neutral info-row variant** — for entities that aren't open/closed states (e.g. doorbell/camera event sensors: visitor, motion, person), use full-width `bubble-card` buttons in their own section (e.g. "Voordeur activiteit") with a neutral tint (`rgba(255,255,255,0.045)` bg) and subtitle "‹duration› geleden" (or "zojuist" under a minute). No green/blue state tint — they're recency info, not status.
- **Header count source** — when the popup shows a set of entities that differs from the group sensor's membership (downstairs' group excludes interior doors), compute the header count/tint from the **explicit list of shown entities** rather than the group's `entity_id` attribute, so the header always agrees with the cards below it. (When the group's membership equals the shown set — garden, upstairs — just use the group.)

## Variations (added while doing the light popups)

Controllable entities (lights) reuse the section-grid + header-summary shell but swap the state card for a **slider card**:

- Card = `custom:bubble-card`, `card_type: button`, `button_type: slider`, `slider_live_update: true`. Drag = brightness; the slider fills and **tints to the light's own `rgb_color`** automatically (do NOT set `use_accent_color`). Off = neutral/empty.
- `tap_action: { action: toggle }`, `double_tap_action` + `hold_action: { action: more-info }` (full controls incl colour/temp).
- **Colour-capable lights** (supported_color_modes includes `xy`/`hs`/`rgb*`) get a `sub_button` `mdi:palette` → `more-info` (colour wheel). Brightness-only lights omit it.
- **Header**: needs an `entity` so the state line renders — point it at any one light; drive count/tint from the explicit shown-list. Warm gold when any on (`rgba(240,195,95,0.13)` bg, `#f0cf8f` text), neutral dim when all off. Count text "N aan · M uit" / "Alles uit".
- Generated with `scratchpad/mk_lights.py` (section → [(entity, name, is_color)]) — reused for beneden/boven/tuin.

## Covers variant (`#screens`)

Covers reuse the light slider card with cover semantics:
- `button_type: slider` on the cover → drag sets position (`set_cover_position`); fill shows how open. `tap_action: toggle` (open↔dicht), `hold_action: more-info`.
- `sub_button` trio ↑ / ■ / ↓ → `perform-action` `cover.open_cover` / `cover.stop_cover` / `cover.close_cover` with `target.entity_id`.
- Subtitle: `open` (pos ≥ 100) / `dicht` (pos ≤ 0) / `N%`; blue when `open`, green when closed (same as doors).
- Header summary "Voor ‹pos› · Zij ‹pos›", tinted blue if any cover `open`.
- Kept the `input_boolean.enable_automatic_screens` toggle (as a `button_type: switch` card under an "Automatisch" separator) and a native `history-graph` under a "Verloop" separator.

## Climate variant (`#klimaat-boven`, `#klimaat-beneden`)

- Thermostat = `button_type: climate` (name, current/target temp, ±, mode) with a power sensor `sub_button`. **Caveat:** Bubble's climate card renders the ±/temp controls **only when the climate is in an active mode** (heat/cool); when `off` or `unavailable` it collapses to just name+icon. So set `tap_action: { action: more-info }` (+ `hold_action` more-info) so it's controllable in every state. (Boven's `climate.eurom_alutherm_baseboard_heater` is seasonally unavailable; beneden's `climate.warmtepomp` is off outside heating/cooling season — both look bare until active.)
- Auxiliary heaters / mode enables = warm toggle cards (`button_type: state`, tap toggle), warm gold when on, subtitle = current power `N W` when on else `uit`; cooling toggle uses the blue palette instead of gold.
- Header: point `entity` at an always-available room temp sensor; show `‹room› ‹temp›°C` + ` · verwarmt`/` · koelt`, tinted warm (heating) / blue (cooling) / dim (off), derived from the climate's `hvac_action`.
- Native cards kept as-is under their own separators: `humidifier`, `statistics-graph`, `history-graph`, and the downstairs `custom:expander-card` "Settings" block.

## Vacuum variant (`#sjorsje`) + action-button pattern

- New popup (the tile previously only opened more-info). Wired the Sjorsje tile `tap_action`/`button_action` → `navigate #sjorsje` and registered the include.
- **Action buttons** (reusable for any stateless command): `button_type: name` card with `tap_action: { action: perform-action, perform_action: <domain.service>, target: { entity_id: … } }` + `hold_action: more-info`. Used for Start / Pauze / Naar dock / Zoek (`vacuum.start` / `pause` / `return_to_base` / `locate`); Start gets a green tint, the rest neutral.
- Header: NL status map from `vacuum.state` (`docked`→Gedockt/Opladen when charging, `cleaning`→Stofzuigen, `returning`→Naar dock, `paused`, `error`→Fout) + battery %, blue when active, red on error.
- Status cards: Accu (battery% + ` · laden`), Stofbak (`binary_sensor.*_bin_full` → red "Vol — legen" / neutral "Leeg"). Stats (missions, cleaning time, battery cycles, energy) in a `custom:expander-card`.
- Sjorsje supports start/pause/stop/return/locate only (no fan-speed/map), so no fan or map controls.

## Out of scope

- The other ~30 popups (energy, climate, lights, people, media, etc.) — they adopt this pattern in later specs/steps.
- Battery/health surfacing beyond what more-info already provides.
- Any control affordances (these entities are read-only).
- Changing widths, modes, or the tile subtitles on the dashboard itself.

## Success criteria

- Both popups render the summary strip + tinted 2-column state cards, no error cards.
- Subtitle shows correct state word + a sensible Dutch duration.
- Open sensors are blue, closed are green; tapping a card opens its more-info.
- Pattern is documented well enough to reuse for the next popup without re-deciding the visual language.
