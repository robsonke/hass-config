# BBQ Popup — Bubble Card UI + Probe-ability Integration

Date: 2026-07-08
Files: `dashboards/popups/pp_bbq_garden.yaml`, `automations.yaml`, `packages/pkg_bbq.yaml`

## Problem

Follow-up to the `2026-07-07-bbq-togrill-thermometer-design.md` migration. Two things prompted this round:

1. The rebuilt BBQ popup still used plain `gauge`/`entities`/`glance` cards, and unavailable sensors (device not powered on) rendered their raw "unavailable" state prominently — the user wants a Bubble Card–based UI with offline entities visually toned down instead of front-and-center.
2. The user has since installed and configured the **Probe-ability** custom integration (`https://github.com/snelstim/Probe-ability`), which predicts meat cook completion time from the same `sensor.probe_1_temperature` / `sensor.probe_2_temperature` / dome ambient sensor, and ships its own Lovelace card (`custom:probe-ability-card`) with a richer UI (current temp, per-cook target, ETA ring timer, carryover-aware pull-from-heat warning) than anything hand-built with Bubble Card would offer for the meat probes specifically.

Investigation confirmed:
- Bubble Card (already installed) exposes `button_type: slider` with `read_only_slider` support for **any** numeric sensor via manual `min_value`/`max_value`, and automatic min/max/step for `number` domain entities — covering both the read-only temperature displays and the interactive device-target controls without custom hacks.
- Styling hooks confirmed against the actual Bubble Card source/docs: `.bubble-icon-container` (icon background), `.bubble-button-card-container` (whole-card background/opacity), `.bubble-range-fill` (slider fill), with JS-template access to `hass.states[...]`, `state`, and `entity` inside `styles:`.
- `horizontal-buttons-stack` (a Bubble Card `card_type`) is a specialized nav/footer component (must be the last card in a view, cannot be nested in a stack) — **not** suitable for pairing two sliders side by side. A native `type: horizontal-stack` (already used elsewhere in this file) is the correct way to lay out the dome min/max sliders.
- Probe-ability is already configured with both probes (config entry "BBQ"): `sensor.tuin_bbq_probe_ability_time_remaining` (probe 1) and `sensor.tuin_bbq_probe_ability_time_remaining_probe_2`, both currently idle/unavailable (no active cook). Its own per-cook target (set via the card's Start Cook UI) is independent of the ToGrill device's onboard target (`number.probe_1/2_target_temperature`).
- The `probe-ability-card.js` resource is not yet registered on the dashboard (unlike `bubble-card.js`, already registered).

## Goals

1. Rebuild the BBQ popup's temperature/targets/notifications sections using Bubble Card, with offline entities visually muted rather than showing raw "unavailable" text.
2. Adopt the Probe-ability card as the primary UI for the two meat probes, replacing the plain temperature display that would otherwise have been hand-built for them.
3. Retire `automation.bbq_probe_1_alarm` and `automation.bbq_probe_2_alarm` — the user decided not to keep the device-onboard-target alarm and Probe-ability's own pull-warning running independently; Probe-ability's in-card warning is now the sole "meat probe" alert path. `automation.bbq_dome_alarm` is untouched (Probe-ability doesn't cover the dome/ambient probe).
4. Register the Probe-ability card's JS resource on the dashboard.
5. Keep the Kookwekker (timer) card and the `mini-graph-card` exactly as they are — out of scope for this round.

## Design

### `dashboards/popups/pp_bbq_garden.yaml`

Replace the current 3-gauge `horizontal-stack` under "Temperaturen" with a single Bubble Card slider for the dome only:

```yaml
- type: custom:bubble-card
  card_type: button
  button_type: slider
  entity: sensor.tuin_bbq_dome_thermometer_ambient_temperature
  name: Dome
  icon: mdi:thermometer
  min_value: 0
  max_value: 400
  read_only_slider: true
  styles: |
    .bubble-icon-container {
      background: ${(hass.states['sensor.dome_alert_temp']?.state === 'Alert') ? '#e74c3c' : 'var(--bubble-icon-background-color)'} !important;
    }
    .bubble-button-card-container {
      opacity: ${(state === 'unavailable' || state === 'unknown') ? 0.4 : 1} !important;
    }
```

Section headers throughout the redesigned popup use a Bubble Card separator (consistent with the rest of the bubble-driven UI, rather than mixing in a plain `entities` card with an empty list as a header hack):

```yaml
- type: custom:bubble-card
  card_type: separator
  name: Vlees voorspelling
```

Add a new "Vlees voorspelling" section directly below the dome slider:

```yaml
- type: vertical-stack
  cards:
    - type: custom:bubble-card
      card_type: separator
      name: Vlees voorspelling
    - type: custom:probe-ability-card
      entity: sensor.tuin_bbq_probe_ability_time_remaining
      probe_sensors:
        - sensor.probe_1_temperature
        - sensor.probe_2_temperature
      ambient_sensor: sensor.tuin_bbq_dome_thermometer_ambient_temperature
```

Replace the "BBQ Targets" / "Vlees Targets" entities cards with a single "Doelen" section — dome min/max only, side by side via a native `horizontal-stack` (not Bubble Card's `horizontal-buttons-stack`, which is unsuitable per the investigation above):

```yaml
- type: vertical-stack
  cards:
    - type: custom:bubble-card
      card_type: separator
      name: Doelen
    - type: horizontal-stack
      cards:
        - type: custom:bubble-card
          card_type: button
          button_type: slider
          entity: number.tuin_bbq_dome_thermometer_ambient_minimum_temperature
          name: Minimaal
        - type: custom:bubble-card
          card_type: button
          button_type: slider
          entity: number.tuin_bbq_dome_thermometer_ambient_maximum_temperature
          name: Maximaal
```

"Notificaties" keeps the same separator-headed section, with the same 4 entities as bubble switch buttons minus the two retired probe alarms:

```yaml
- type: vertical-stack
  cards:
    - type: custom:bubble-card
      card_type: separator
      name: Notificaties
    - type: custom:bubble-card
      card_type: button
      entity: input_boolean.enable_bbq_automations
      name: Alle notificaties?
    - type: custom:bubble-card
      card_type: button
      entity: automation.bbq_timer_notifications
      name: Timer
    - type: custom:bubble-card
      card_type: button
      entity: automation.bbq_dome_alarm
      name: Dome alarm
```

Register the resource (via `ha_config_set_dashboard_resource` during implementation):
- URL: `/probe_ability/probe-ability-card.js`, type: JavaScript module.

### `automations.yaml`

Remove the `BBQ - Probe 1 alarm` (id `1690718896889`) and `BBQ - Probe 2 alarm` (id `1690720476474`) automations entirely. `BBQ - Dome alarm` (id `1720370000001`) and `BBQ - Timer notifications` are untouched.

### `packages/pkg_bbq.yaml`

Remove the `sensor.target_alert_temp_probe_1` and `sensor.target_alert_temp_probe_2` template sensors — nothing references them once the two automations above and the old dashboard cards are gone. Keep `sensor.dome_alert_temp` (still used by `BBQ - Dome alarm` and the dome slider's icon-color style) untouched, along with `timer.bbq` and `input_boolean.enable_bbq_automations`.

### Non-goals / explicitly out of scope

- No change to `timer.bbq` (Kookwekker) or the `mini-graph-card`.
- No change to `automation.bbq_dome_alarm` or its underlying template sensor.
- No attempt to sync Probe-ability's per-cook target with the device's onboard `number.probe_1/2_target_temperature` — they remain fully independent; the device's onboard target is no longer surfaced in the HA dashboard at all (per the user's choice), though it still exists and could still drive the physical device's own alarm if set via the ToGrill app directly.

## Testing / Verification Plan

- Validate YAML syntax for all three files.
- Reload automations/templates via Home Assistant; confirm no errors and that the removed entities (`sensor.target_alert_temp_probe_1/2`, the two alarm automations) are actually gone from the state machine, not just absent from new config.
- Register the `probe-ability-card.js` dashboard resource and confirm it doesn't collide with an existing resource entry.
- Config-only verification: neither the physical ToGrill device nor an active Probe-ability cook can be exercised live in this session — confirm entity references resolve and the dashboard YAML parses without card errors.
