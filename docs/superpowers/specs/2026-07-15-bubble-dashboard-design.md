# Bubble Card Dashboard — Replacing Mushroom as the Experimental Dashboard

Date: 2026-07-15
Files: `configuration.yaml` (dashboard registration), `dashboards/mushroom-dashboard.yaml` (deleted), `dashboards/bubble-dashboard.yaml` (new)

## Problem

`dashboards/mushroom-dashboard.yaml` was built as an experimental alternative to `dashboards/main-dashboard.yaml`, using `custom:mushroom-*` cards in HA's native `sections` view. Bubble Card is already installed via HACS, registered as a dashboard resource, and has already been partially adopted in a couple of popups (`pp_bbq_garden.yaml`, `pp_footer_stookalert.yaml`, and the recent BBQ/cats popup redesigns). The user wants to retire the Mushroom experiment and stand up a new Bubble Card–based experimental dashboard in its place, covering the same ground as `main-dashboard.yaml`.

## Goals

1. Delete `dashboards/mushroom-dashboard.yaml` and remove its `lovelace-mushroom` entry from `configuration.yaml`.
2. Add a new `lovelace-bubble` dashboard entry in `configuration.yaml` pointing at `dashboards/bubble-dashboard.yaml`, titled "Bubble", icon `mdi:chart-bubble`, `show_in_sidebar: true`, `require_admin: false` — taking Mushroom's old slot.
3. Rebuild `main-dashboard.yaml`'s content (not `main-dashboard.yaml` itself, which stays untouched) as `dashboards/bubble-dashboard.yaml`, using HA's native `sections` view (as Mushroom did) rather than main-dashboard's custom CSS grid-layout.
4. Full content parity with `main-dashboard.yaml`: status row, Weer & Mensen, Huis, Beneden, Boven, Tuin (x2), Energie.
5. All existing `popups/pp_*.yaml` are reused unchanged via `tap_action`/`icon_tap_action` — popup content/migration is explicitly out of scope here.

## Non-goals / explicitly out of scope

- No changes to `main-dashboard.yaml` — it keeps running as the daily-driver dashboard. This is a parallel experiment, not a cutover (yet).
- No popup content changes.
- No replicating `custom:button-card` template's bespoke visual polish (blinking alarm icon, circular BMW charge gauge, `group_expand` inline entity lists, etc.) in v1. These become separate follow-up specs once the base dashboard has been used day-to-day, matching how the BBQ/cats popups were iterated.
- No `custom:navbar-card` footer and no `custom:anchor-card` scroll-links — this dashboard has no fixed footer at all.

## Design

### Dashboard registration (`configuration.yaml`)

Replace:
```yaml
lovelace:
  mode: storage
  dashboards:
    lovelace-mushroom:
      mode: yaml
      filename: dashboards/mushroom-dashboard.yaml
      title: Mushroom
      icon: mdi:mushroom
      show_in_sidebar: true
      require_admin: false
    lovelace-main:
      ...
```
with:
```yaml
lovelace:
  mode: storage
  dashboards:
    lovelace-bubble:
      mode: yaml
      filename: dashboards/bubble-dashboard.yaml
      title: Bubble
      icon: mdi:chart-bubble
      show_in_sidebar: true
      require_admin: false
    lovelace-main:
      ...
```

### Layout: native `sections` view, single column per section, stacked rows

Confirmed via mockup review: each section is a full-width stack of one bubble button per row (name + state clearly visible), not a 2-up grid. This is closer to Bubble Card's usual community look than main-dashboard's dense 2-column grid, and reads better on mobile.

```yaml
views:
  - type: sections
    title: Bubble
    path: bubble
    theme: Frosted Glass Dark
    max_columns: 4
    sections:
      - cards: [...]   # Status row
      - title: Weer & Mensen
        cards: [...]
      - title: Huis
        cards: [...]
      - title: Beneden
        cards: [...]
      - title: Boven
        cards: [...]
      - title: Tuin
        cards: [...]
      - title: " "        # second Tuin column (cats/bbq/lawn mower/irrigation), mirrors main-dashboard's garden1/garden2 split
        cards: [...]
      - title: Energie
        cards: [...]
```

### Status row — replaces the footer

Since there's no fixed footer in this dashboard, Settings and Stookwijzer move into the top status row as small icon-only bubble buttons, alongside the existing alarm/persons/doors/power/updates chips:

```yaml
- cards:
    - type: horizontal-stack
      cards:
        - type: custom:bubble-card
          card_type: button
          button_type: state
          entity: alarm_control_panel.alarmo
          show_name: false
          show_state: false
          icon: mdi:shield-home
          tap_action:
            !include popups/pp_alarm.yaml
        - type: custom:bubble-card
          card_type: button
          button_type: state
          entity: person.rob
          show_name: false
          tap_action:
            !include popups/pp_person_rob.yaml
        - type: custom:bubble-card
          card_type: button
          button_type: state
          entity: person.steffi
          show_name: false
          tap_action:
            !include popups/pp_person_steffi.yaml
        - type: custom:bubble-card
          card_type: button
          button_type: state
          entity: sensor.open_windows_and_doors
          show_name: false
          icon: mdi:door-open
          tap_action:
            !include popups/pp_doors_downstairs.yaml
        - type: custom:bubble-card
          card_type: button
          button_type: state
          entity: sensor.net_power_consumption
          show_name: false
          icon: mdi:lightning-bolt
          tap_action:
            !include popups/pp_energy_usage.yaml
        - type: custom:bubble-card
          card_type: button
          button_type: state
          entity: sensor.all_updates
          show_name: false
          icon: mdi:repeat-off
          tap_action:
            !include popups/pp_footer_update.yaml
        - type: custom:bubble-card
          card_type: button
          button_type: name
          show_name: false
          icon: mdi:cog-outline
          tap_action:
            !include popups/pp_footer_system.yaml
        - type: custom:bubble-card
          card_type: button
          button_type: state
          entity: sensor.stookwijzer
          show_name: false
          icon: mdi:fire
          tap_action:
            !include popups/pp_footer_stookalert.yaml
```
(exact `button_type`/state-display choices get finalized during implementation against live entity states — this shows the structural pattern.)

### Weer & Mensen

Kept as-is — not mushroom-specific, no bubble equivalent needed: `custom:clock-weather-card`, `tile` cards for kid cameras, `custom:trash-card`. Only the `custom:mushroom-person-card` and `custom:mushroom-vacuum-card`/`custom:mushroom-entity-card` rows get swapped for `custom:bubble-card` `button` cards (one row each, per the density decision above).

### Huis / Beneden / Boven / Tuin / Energie

Each entity row becomes one full-width `custom:bubble-card`:

| Entity type | `card_type` | Notes |
|---|---|---|
| Alarm, generic sensors/binary_sensors, presence, picnic, water, updates | `button` (`button_type: state` or `name`) | tap opens existing popup |
| Lights (`light.lights_*` groups) | `button` (`button_type: switch` or `slider`) | tap opens existing popup (lists individual lights) — no inline group-expand in v1 |
| Covers (`cover.covers_downstairs`) | `cover` | native open/close/stop/tilt controls |
| Climate (`sensor.indoor_temperature` / `climate.eurom_alutherm_baseboard_heater`) | `climate` | tap opens existing popup |
| Media players (Sonos) | `media-player` | |
| Doors/windows binary groups | `button` (`button_type: state`) | tap opens existing popup |
| Pool, cats, BBQ, lawn mower, irrigation | `button` / `separator` mix | follows the pattern already used in `pp_bbq_garden.yaml` |

### Testing / Verification Plan

- Validate YAML syntax of `configuration.yaml` and `dashboards/bubble-dashboard.yaml` (matches CI's Super Linter + Frenck HA config check).
- Confirm `configuration.yaml` no longer references `dashboards/mushroom-dashboard.yaml` and the file is deleted.
- Reload dashboards in HA, confirm "Bubble" appears in the sidebar (Mushroom no longer does) and "Home" (main-dashboard) is unaffected.
- Visually walk every section, confirming: correct entity, correct icon/state rendering, every `tap_action` opens the correct existing popup unchanged.
- Confirm Settings and Stookwijzer are reachable from the status row.
