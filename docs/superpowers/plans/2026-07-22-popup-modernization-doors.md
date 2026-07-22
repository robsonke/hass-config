# Door/window popup modernization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the two door/window Bubble Card pop-ups (`#deuren-tuin`, `#ramen-boven`) as a glanceable "state-card grid" — a summary strip, area sections, and 2-column state-tinted cards showing open/closed + duration.

**Architecture:** Each pop-up's `cards:` becomes: a summary strip (group sensor), then per area a `card_type: separator` label + a native `type: grid` (columns: 2) of `custom:bubble-card` state buttons. State tint + duration subtitle are done in each card's `styles:` block with `${…}` JS templating (`state`, `hass` in scope). Cards are read-only; tap opens HA more-info.

**Tech Stack:** Home Assistant YAML-mode Lovelace, Bubble Card v3.2.0 (`custom:bubble-card`), native `grid` card. No build step. "Tests" = YAML parse validation + live verification in the controlled browser tab against `http://192.168.0.40:8123/lovelace-bubble/overzicht`.

## Global Constraints

- Files live in `dashboards/popups/`; the dashboard `dashboards/bubble-dashboard.yaml` already `!include`s both via existing lines — do **not** change includes or the dashboard tiles.
- Keep each file's existing header keys: `type: custom:bubble-card`, `card_type: pop-up`, `popup_mode: centered`, `full_width_on_mobile: true`, its `width_desktop`, `hash`, `name`, `icon`.
- Dutch UI copy. State words: `open` / `dicht`. Duration: `net` / `N min` / `N uur` / `1 dag` / `N dagen`.
- Tint (translucent, no glow): closed bg `rgba(45,170,115,0.13)` / icon `rgba(45,170,115,0.20)` / subtitle `#8fbda6`; open bg `rgba(238,160,55,0.16)` / icon `rgba(238,160,55,0.22)` / subtitle `#e0ac6a`.
- After editing an `!include`d file, run `touch dashboards/bubble-dashboard.yaml` so HA re-reads the YAML config, then reload the browser (navigate away to `/lovelace/0` and back to bust the occasional stuck-blank state).
- Nothing gets committed to git beyond the two popup files in these tasks; do not run `./gitupdate.sh`.

---

### Task 1: Garden doors popup (`#deuren-tuin`)

Establishes the state-card grid pattern on the simplest popup: one section, two door cards, plus the summary strip.

**Files:**
- Modify (full rewrite): `dashboards/popups/bpp_doors_garden.yaml`

**Interfaces:**
- Consumes: `binary_sensor.doors_and_windows_garden` (group, has `attributes.entity_id` member list), `binary_sensor.sheddoor_openclose_contact` ("Schuurdeur"), `binary_sensor.cabindoor_openclose_contact` ("Blokhutdeur").
- Produces: the reusable card/summary/section snippets that Task 2 copies verbatim (Bubble has no shared-macro mechanism, so the JS duration helper and tint rules are repeated per card by design).

- [ ] **Step 1: Write the file**

Replace the entire contents of `dashboards/popups/bpp_doors_garden.yaml` with:

```yaml
# Bubble Card native pop-up (hash #deuren-tuin) — Deuren tile (Tuin).
# State-card grid pattern — see docs/superpowers/specs/2026-07-22-popup-modernization-doors-design.md
type: custom:bubble-card
card_type: pop-up
popup_mode: centered
full_width_on_mobile: true
width_desktop: 680px
hash: '#deuren-tuin'
name: Deuren in de tuin
icon: mdi:door-sliding
cards:
  # ── summary strip (green = alles dicht, amber = iets open) ─────────
  - type: custom:bubble-card
    card_type: button
    button_type: state
    entity: binary_sensor.doors_and_windows_garden
    card_layout: large
    show_name: false
    styles: |
      .bubble-button-background { opacity: 1 !important; background-color: ${state === 'on' ? 'rgba(238,160,55,0.16)' : 'rgba(45,170,115,0.13)'} !important; }
      .bubble-icon-container { background-color: ${state === 'on' ? 'rgba(238,160,55,0.22)' : 'rgba(45,170,115,0.20)'} !important; }
      .bubble-state { font-size: 0 !important; }
      .bubble-state::after {
        font-size: 15px !important; font-weight: 500;
        color: ${state === 'on' ? '#e6b876' : '#9ed9bd'} !important;
        content: "${(() => { const g = hass.states['binary_sensor.doors_and_windows_garden']; const m = (g?.attributes?.entity_id) || []; const o = m.filter(e => hass.states[e]?.state === 'on').length; return o === 0 ? 'Alles dicht' : o + ' open · ' + (m.length - o) + ' dicht'; })()}";
      }
  # ── section: Schuurdeuren ─────────────────────────────────────────
  - type: custom:bubble-card
    card_type: separator
    name: Schuurdeuren
  - type: grid
    columns: 2
    square: false
    cards:
      - type: custom:bubble-card
        card_type: button
        button_type: state
        entity: binary_sensor.sheddoor_openclose_contact
        name: Schuurdeur
        card_layout: large
        tap_action: { action: more-info }
        button_action:
          tap_action: { action: more-info }
        styles: |
          .bubble-button-background { opacity: 1 !important; background-color: ${state === 'on' ? 'rgba(238,160,55,0.16)' : 'rgba(45,170,115,0.13)'} !important; }
          .bubble-icon-container { background-color: ${state === 'on' ? 'rgba(238,160,55,0.22)' : 'rgba(45,170,115,0.20)'} !important; }
          .bubble-state { font-size: 0 !important; }
          .bubble-state::after { font-size: 12.5px !important; color: ${state === 'on' ? '#e0ac6a' : '#8fbda6'} !important; content: "${(() => { const w = state === 'on' ? 'open' : 'dicht'; const t = hass.states['binary_sensor.sheddoor_openclose_contact']?.last_changed; const s = (Date.now() - new Date(t)) / 1000; let d; if (s < 60) d = 'net'; else if (s < 3600) { const m = Math.round(s/60); d = m >= 60 ? '1 uur' : m + ' min'; } else if (s < 86400) { const h = Math.round(s/3600); d = h >= 24 ? '1 dag' : h + ' uur'; } else { const dy = Math.round(s/86400); d = dy + (dy === 1 ? ' dag' : ' dagen'); } return w + ' · ' + d; })()}"; }
      - type: custom:bubble-card
        card_type: button
        button_type: state
        entity: binary_sensor.cabindoor_openclose_contact
        name: Blokhutdeur
        card_layout: large
        tap_action: { action: more-info }
        button_action:
          tap_action: { action: more-info }
        styles: |
          .bubble-button-background { opacity: 1 !important; background-color: ${state === 'on' ? 'rgba(238,160,55,0.16)' : 'rgba(45,170,115,0.13)'} !important; }
          .bubble-icon-container { background-color: ${state === 'on' ? 'rgba(238,160,55,0.22)' : 'rgba(45,170,115,0.20)'} !important; }
          .bubble-state { font-size: 0 !important; }
          .bubble-state::after { font-size: 12.5px !important; color: ${state === 'on' ? '#e0ac6a' : '#8fbda6'} !important; content: "${(() => { const w = state === 'on' ? 'open' : 'dicht'; const t = hass.states['binary_sensor.cabindoor_openclose_contact']?.last_changed; const s = (Date.now() - new Date(t)) / 1000; let d; if (s < 60) d = 'net'; else if (s < 3600) { const m = Math.round(s/60); d = m >= 60 ? '1 uur' : m + ' min'; } else if (s < 86400) { const h = Math.round(s/3600); d = h >= 24 ? '1 dag' : h + ' uur'; } else { const dy = Math.round(s/86400); d = dy + (dy === 1 ? ' dag' : ' dagen'); } return w + ' · ' + d; })()}"; }
```

- [ ] **Step 2: Validate YAML parses**

Run:
```bash
cd /Volumes/config && python3 -c "import yaml
class L(yaml.SafeLoader): pass
for t in ['!secret','!include','!include_dir_merge_named']: L.add_constructor(t, lambda l,n: None)
d=yaml.load(open('dashboards/popups/bpp_doors_garden.yaml'),Loader=L)
assert d['card_type']=='pop-up' and d['hash']=='#deuren-tuin' and d['cards']
print('OK', len(d['cards']), 'top-level cards')"
```
Expected: `OK 3 top-level cards` (summary, separator, grid).

- [ ] **Step 3: Re-read config + reload**

Run:
```bash
cd /Volumes/config && touch dashboards/bubble-dashboard.yaml && echo touched
```
Then in the browser: navigate to `http://192.168.0.40:8123/lovelace/0`, then to `http://192.168.0.40:8123/lovelace-bubble/overzicht#deuren-tuin`, wait ~6s for hydration.

- [ ] **Step 4: Verify live**

Screenshot the open pop-up and confirm:
- Summary strip reads "Alles dicht" (both closed) or "N open · M dicht", tinted green/amber accordingly.
- Section label "SCHUURDEUREN" above a 2-column row.
- Two cards "Schuurdeur" / "Blokhutdeur", each green-tinted with subtitle `dicht · <duration>`; icon shows a door.
- No `hui-error-card` in the pop-up (JS check: walk shadow DOM for the `#deuren-tuin` bubble-card, assert 0 error cards).
- Tapping a card opens the HA more-info dialog for that sensor.

If cards look too tall/cramped, adjust `card_layout` (drop it for a shorter row) and re-verify — do not change entities or tints.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/config && git add dashboards/popups/bpp_doors_garden.yaml && git commit -m "Modernize garden doors popup — state-card grid

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Upstairs doors/windows popup (`#ramen-boven`)

Applies the same pattern with two sections and five window cards.

**Files:**
- Modify (full rewrite): `dashboards/popups/bpp_doors_upstairs.yaml`

**Interfaces:**
- Consumes: `binary_sensor.doors_and_windows_upstairs` (group), and windows `window_masterbed_1_openclose_contact` ("Raam 1"), `window_masterbed_2_openclose_contact` ("Raam 2"), `window_eva_openclose_contact` ("Eva"), `window_noaroom_openclose_contact` ("Noa"), `window_guestroom_openclose_contact` ("Logeerkamer").
- Produces: nothing downstream (final task).

- [ ] **Step 1: Write the file**

Replace the entire contents of `dashboards/popups/bpp_doors_upstairs.yaml` with:

```yaml
# Bubble Card native pop-up (hash #ramen-boven) — Ramen tile (Boven).
# State-card grid pattern — see docs/superpowers/specs/2026-07-22-popup-modernization-doors-design.md
type: custom:bubble-card
card_type: pop-up
popup_mode: centered
full_width_on_mobile: true
width_desktop: 760px
hash: '#ramen-boven'
name: Deuren en ramen boven
icon: mdi:window-closed-variant
cards:
  # ── summary strip ─────────────────────────────────────────────────
  - type: custom:bubble-card
    card_type: button
    button_type: state
    entity: binary_sensor.doors_and_windows_upstairs
    card_layout: large
    show_name: false
    styles: |
      .bubble-button-background { opacity: 1 !important; background-color: ${state === 'on' ? 'rgba(238,160,55,0.16)' : 'rgba(45,170,115,0.13)'} !important; }
      .bubble-icon-container { background-color: ${state === 'on' ? 'rgba(238,160,55,0.22)' : 'rgba(45,170,115,0.20)'} !important; }
      .bubble-state { font-size: 0 !important; }
      .bubble-state::after {
        font-size: 15px !important; font-weight: 500;
        color: ${state === 'on' ? '#e6b876' : '#9ed9bd'} !important;
        content: "${(() => { const g = hass.states['binary_sensor.doors_and_windows_upstairs']; const m = (g?.attributes?.entity_id) || []; const o = m.filter(e => hass.states[e]?.state === 'on').length; return o === 0 ? 'Alles dicht' : o + ' open · ' + (m.length - o) + ' dicht'; })()}";
      }
  # ── section: Master bedroom ───────────────────────────────────────
  - type: custom:bubble-card
    card_type: separator
    name: Master bedroom
  - type: grid
    columns: 2
    square: false
    cards:
      - type: custom:bubble-card
        card_type: button
        button_type: state
        entity: binary_sensor.window_masterbed_1_openclose_contact
        name: Raam 1
        card_layout: large
        tap_action: { action: more-info }
        button_action:
          tap_action: { action: more-info }
        styles: |
          .bubble-button-background { opacity: 1 !important; background-color: ${state === 'on' ? 'rgba(238,160,55,0.16)' : 'rgba(45,170,115,0.13)'} !important; }
          .bubble-icon-container { background-color: ${state === 'on' ? 'rgba(238,160,55,0.22)' : 'rgba(45,170,115,0.20)'} !important; }
          .bubble-state { font-size: 0 !important; }
          .bubble-state::after { font-size: 12.5px !important; color: ${state === 'on' ? '#e0ac6a' : '#8fbda6'} !important; content: "${(() => { const w = state === 'on' ? 'open' : 'dicht'; const t = hass.states['binary_sensor.window_masterbed_1_openclose_contact']?.last_changed; const s = (Date.now() - new Date(t)) / 1000; let d; if (s < 60) d = 'net'; else if (s < 3600) { const m = Math.round(s/60); d = m >= 60 ? '1 uur' : m + ' min'; } else if (s < 86400) { const h = Math.round(s/3600); d = h >= 24 ? '1 dag' : h + ' uur'; } else { const dy = Math.round(s/86400); d = dy + (dy === 1 ? ' dag' : ' dagen'); } return w + ' · ' + d; })()}"; }
      - type: custom:bubble-card
        card_type: button
        button_type: state
        entity: binary_sensor.window_masterbed_2_openclose_contact
        name: Raam 2
        card_layout: large
        tap_action: { action: more-info }
        button_action:
          tap_action: { action: more-info }
        styles: |
          .bubble-button-background { opacity: 1 !important; background-color: ${state === 'on' ? 'rgba(238,160,55,0.16)' : 'rgba(45,170,115,0.13)'} !important; }
          .bubble-icon-container { background-color: ${state === 'on' ? 'rgba(238,160,55,0.22)' : 'rgba(45,170,115,0.20)'} !important; }
          .bubble-state { font-size: 0 !important; }
          .bubble-state::after { font-size: 12.5px !important; color: ${state === 'on' ? '#e0ac6a' : '#8fbda6'} !important; content: "${(() => { const w = state === 'on' ? 'open' : 'dicht'; const t = hass.states['binary_sensor.window_masterbed_2_openclose_contact']?.last_changed; const s = (Date.now() - new Date(t)) / 1000; let d; if (s < 60) d = 'net'; else if (s < 3600) { const m = Math.round(s/60); d = m >= 60 ? '1 uur' : m + ' min'; } else if (s < 86400) { const h = Math.round(s/3600); d = h >= 24 ? '1 dag' : h + ' uur'; } else { const dy = Math.round(s/86400); d = dy + (dy === 1 ? ' dag' : ' dagen'); } return w + ' · ' + d; })()}"; }
  # ── section: Overig ───────────────────────────────────────────────
  - type: custom:bubble-card
    card_type: separator
    name: Overig
  - type: grid
    columns: 2
    square: false
    cards:
      - type: custom:bubble-card
        card_type: button
        button_type: state
        entity: binary_sensor.window_eva_openclose_contact
        name: Eva
        card_layout: large
        tap_action: { action: more-info }
        button_action:
          tap_action: { action: more-info }
        styles: |
          .bubble-button-background { opacity: 1 !important; background-color: ${state === 'on' ? 'rgba(238,160,55,0.16)' : 'rgba(45,170,115,0.13)'} !important; }
          .bubble-icon-container { background-color: ${state === 'on' ? 'rgba(238,160,55,0.22)' : 'rgba(45,170,115,0.20)'} !important; }
          .bubble-state { font-size: 0 !important; }
          .bubble-state::after { font-size: 12.5px !important; color: ${state === 'on' ? '#e0ac6a' : '#8fbda6'} !important; content: "${(() => { const w = state === 'on' ? 'open' : 'dicht'; const t = hass.states['binary_sensor.window_eva_openclose_contact']?.last_changed; const s = (Date.now() - new Date(t)) / 1000; let d; if (s < 60) d = 'net'; else if (s < 3600) { const m = Math.round(s/60); d = m >= 60 ? '1 uur' : m + ' min'; } else if (s < 86400) { const h = Math.round(s/3600); d = h >= 24 ? '1 dag' : h + ' uur'; } else { const dy = Math.round(s/86400); d = dy + (dy === 1 ? ' dag' : ' dagen'); } return w + ' · ' + d; })()}"; }
      - type: custom:bubble-card
        card_type: button
        button_type: state
        entity: binary_sensor.window_noaroom_openclose_contact
        name: Noa
        card_layout: large
        tap_action: { action: more-info }
        button_action:
          tap_action: { action: more-info }
        styles: |
          .bubble-button-background { opacity: 1 !important; background-color: ${state === 'on' ? 'rgba(238,160,55,0.16)' : 'rgba(45,170,115,0.13)'} !important; }
          .bubble-icon-container { background-color: ${state === 'on' ? 'rgba(238,160,55,0.22)' : 'rgba(45,170,115,0.20)'} !important; }
          .bubble-state { font-size: 0 !important; }
          .bubble-state::after { font-size: 12.5px !important; color: ${state === 'on' ? '#e0ac6a' : '#8fbda6'} !important; content: "${(() => { const w = state === 'on' ? 'open' : 'dicht'; const t = hass.states['binary_sensor.window_noaroom_openclose_contact']?.last_changed; const s = (Date.now() - new Date(t)) / 1000; let d; if (s < 60) d = 'net'; else if (s < 3600) { const m = Math.round(s/60); d = m >= 60 ? '1 uur' : m + ' min'; } else if (s < 86400) { const h = Math.round(s/3600); d = h >= 24 ? '1 dag' : h + ' uur'; } else { const dy = Math.round(s/86400); d = dy + (dy === 1 ? ' dag' : ' dagen'); } return w + ' · ' + d; })()}"; }
      - type: custom:bubble-card
        card_type: button
        button_type: state
        entity: binary_sensor.window_guestroom_openclose_contact
        name: Logeerkamer
        card_layout: large
        tap_action: { action: more-info }
        button_action:
          tap_action: { action: more-info }
        styles: |
          .bubble-button-background { opacity: 1 !important; background-color: ${state === 'on' ? 'rgba(238,160,55,0.16)' : 'rgba(45,170,115,0.13)'} !important; }
          .bubble-icon-container { background-color: ${state === 'on' ? 'rgba(238,160,55,0.22)' : 'rgba(45,170,115,0.20)'} !important; }
          .bubble-state { font-size: 0 !important; }
          .bubble-state::after { font-size: 12.5px !important; color: ${state === 'on' ? '#e0ac6a' : '#8fbda6'} !important; content: "${(() => { const w = state === 'on' ? 'open' : 'dicht'; const t = hass.states['binary_sensor.window_guestroom_openclose_contact']?.last_changed; const s = (Date.now() - new Date(t)) / 1000; let d; if (s < 60) d = 'net'; else if (s < 3600) { const m = Math.round(s/60); d = m >= 60 ? '1 uur' : m + ' min'; } else if (s < 86400) { const h = Math.round(s/3600); d = h >= 24 ? '1 dag' : h + ' uur'; } else { const dy = Math.round(s/86400); d = dy + (dy === 1 ? ' dag' : ' dagen'); } return w + ' · ' + d; })()}"; }
```

- [ ] **Step 2: Validate YAML parses**

Run:
```bash
cd /Volumes/config && python3 -c "import yaml
class L(yaml.SafeLoader): pass
for t in ['!secret','!include','!include_dir_merge_named']: L.add_constructor(t, lambda l,n: None)
d=yaml.load(open('dashboards/popups/bpp_doors_upstairs.yaml'),Loader=L)
assert d['card_type']=='pop-up' and d['hash']=='#ramen-boven' and len(d['cards'])==5
print('OK', len(d['cards']), 'top-level cards')"
```
Expected: `OK 5 top-level cards` (summary, sep, grid, sep, grid).

- [ ] **Step 3: Re-read config + reload**

Run:
```bash
cd /Volumes/config && touch dashboards/bubble-dashboard.yaml && echo touched
```
Then in the browser: navigate to `http://192.168.0.40:8123/lovelace/0`, then `http://192.168.0.40:8123/lovelace-bubble/overzicht#ramen-boven`, wait ~6s.

- [ ] **Step 4: Verify live**

Screenshot and confirm:
- Summary strip shows the correct count (Slaapkamerraam 1 is currently `on`, so expect "1 open · 4 dicht", amber-tinted).
- Two sections "MASTER BEDROOM" (Raam 1 / Raam 2) and "OVERIG" (Eva / Noa / Logeerkamer), each a 2-column grid (Overig's third card wraps to a new row).
- Raam 1 amber (`open · <dur>`), the rest green (`dicht · <dur>`); window icons reflect open/closed.
- No `hui-error-card`; tapping a card opens more-info.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/config && git add dashboards/popups/bpp_doors_upstairs.yaml && git commit -m "Modernize upstairs doors/windows popup — state-card grid

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review notes

- **Spec coverage:** summary strip (both tasks), area sections + labels (Schuurdeuren / Master bedroom / Overig), 2-col state-card grid, state+duration subtitle, green/amber tint, tap→more-info, kept header keys/widths — all present. Reusable pattern is realized by Task 1 and copied in Task 2.
- **Placeholder scan:** the only conditional tuning is Task 1 Step 4's "drop `card_layout` if too tall" — that's a verification adjustment, not an unspecified requirement; tints/entities/copy are fully specified.
- **Consistency:** identical tint hex values, subtitle color hex, and duration helper across every card and both files; entity IDs match the spec's friendly-name mapping.
