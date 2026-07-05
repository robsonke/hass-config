# "Cats" Popup — Bubble Card Layout

Date: 2026-07-05
File: `templates/button_card_templates/tpl_main.yaml` (the `cats` button-card template, lines ~117-158)

## Problem

The `cats` template's popup (triggered from the "Boris&Puk" card on `dashboards/main-dashboard.yaml`) currently shows:

1. A `custom:more-info-card` for `binary_sensor.motion_sensor_cats_occupancy` ("Luikje").
2. An `entities` card referencing `sensor.boris_tracker_battery`.
3. A `map` card.

Investigation found two problems with the current content:

- `sensor.boris_tracker_battery` **no longer exists** in Home Assistant — that tracker hardware/integration is gone, so the entities card row is broken.
- `binary_sensor.motion_sensor_cats_occupancy` ("Luik Boris & Puk") is currently in state `unavailable` (device offline), independent of this change.

The user wants the map removed and the popup rebuilt with a Bubble Card–based layout, matching the style already established in this repo (`dashboards/popups/pp_footer_stookalert.yaml` uses `custom:bubble-card` buttons with state-based background coloring for `sensor.stookwijzer`). Bubble Card is already installed via HACS and registered as a dashboard resource — no new resource setup needed.

## Goals

1. Remove the `map` card and the dead `sensor.boris_tracker_battery` entities card.
2. Replace the `more-info-card` with a Bubble Card button showing the flap sensor's state, color-coded (green = cat present, grey = idle, red = unavailable), plus a relative last-changed time.
3. Add a second Bubble Card button showing today's flap-use count from the existing `sensor.cat_door_today`.
4. Keep everything else about the `cats` template unchanged: the circle display on the dashboard card itself, the popup title ("Boris en Puk"), and the `tap_action`/`browser_mod.popup` wiring.
5. Out of scope (explicitly deferred): bijkeuken camera sighting count/snapshot content — that belongs to the separate "cat sighting gallery" follow-up task.

## Design

Replace the `content.cards` list under the `cats` template's `tap_action.browser_mod.data.content` in `templates/button_card_templates/tpl_main.yaml` with:

```yaml
content:
  type: vertical-stack
  cards:
    - type: custom:bubble-card
      card_type: button
      button_type: state
      entity: binary_sensor.motion_sensor_cats_occupancy
      name: Luikje
      icon: mdi:cat
      show_state: true
      show_last_changed: true
      styles: |
        .bubble-button-background {
          opacity: 1 !important;
          background-color: ${(state === 'on' ? '#2ecc71' : state === 'off' ? '#7f8c8d' : '#e74c3c')} !important;
        }
    - type: custom:bubble-card
      card_type: separator
    - type: custom:bubble-card
      card_type: button
      button_type: state
      entity: sensor.cat_door_today
      name: Vandaag door het luikje
      icon: mdi:door
      show_state: true
```

Everything above `content:` (the `template`, `variables`, `state_display`, `tap_action.action`/`browser_mod.service`/`data.size`/`data.timeout`/`data.title`) stays exactly as-is.

### Non-goals / explicitly out of scope

- No changes to the dashboard card's circle display (the `circle_text`/`circle_input` variables).
- No bijkeuken camera sighting count or snapshot image in this popup (deferred to the later gallery task).
- No replacement tracker/battery entity — dropped entirely per the user's decision, since no working hardware currently exists.

## Testing / Verification Plan

- Validate YAML syntax of `templates/button_card_templates/tpl_main.yaml`.
- Confirm the dashboard reloads the template without lint/parse errors.
- Visually confirm in the dashboard: tapping the "Boris&Puk" card opens the popup, showing the two bubble-card buttons (flap state color-coded, door count) and no map or dead entity row.
