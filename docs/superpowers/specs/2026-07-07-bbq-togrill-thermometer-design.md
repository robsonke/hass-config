# BBQ Thermometer Migration — ToGrill Device

Date: 2026-07-07
Files: `packages/pkg_bbq.yaml`, `automations.yaml`, `dashboards/popups/pp_bbq_garden.yaml`

## Problem

The BBQ setup is moving from an Inkbird IBT-2X (2 probes, `sensor.inkbird_ibt_2x_temperature_probe_1` placed inside the dome for an ambient reading, `sensor.inkbird_ibt_2x_temperature_probe_2` in the meat) to a new **ToGrill** Bluetooth thermometer (`platform: togrill`) — one physical device (MAC `E4:E8:05:4A:75:14`) with 3 channels:

- `sensor.tuin_bbq_dome_thermometer_ambient_temperature` — a dedicated ambient/dome sensor built into the unit (no probe placement needed for this reading anymore).
- `sensor.probe_1_temperature` / `sensor.probe_2_temperature` — two independent meat probes, now both free for meat since the dome no longer needs one of them.

The user's original question was how to keep the device's own on-device alarm in sync with Home Assistant's automation-based alarm. Investigation found this is already solved by the integration: the device's min/max/target thresholds are exposed as **`number` entities** (not read-only sensors) — `number.tuin_bbq_dome_thermometer_ambient_minimum_temperature` / `_maximum_temperature`, `number.probe_1_target_temperature` / `_minimum_temperature` / `_maximum_temperature`, and the equivalent `number.probe_2_*`. Setting these from Home Assistant writes through to the device, so there is only ever one threshold value — nothing to keep in sync as long as HA reads/writes these entities directly instead of maintaining a separate copy.

Native ranges reported by the entities (confirmed via live state attributes): dome min/max `0–400°C` step `1`; both probes' min/max/target `0–250°C` step `1`.

## Goals

1. Retire the old Inkbird-based sensors/thresholds in favor of the new ToGrill entities.
2. Eliminate duplicate threshold storage — read/write the device's native `number.*` entities directly everywhere (automations and dashboard), instead of maintaining parallel `input_number` helpers.
3. Rebuild the 3 alarm automations around the new dome/probe-1/probe-2 mapping (previously 2 automations existed, for dome and one meat probe; now 3 are needed since both probes are meat).
4. Update the BBQ dashboard popup for 3 temperature channels instead of 2, with target/threshold controls pointed at the native number entities.
5. Keep `timer.bbq` (kookwekker) and `input_boolean.enable_bbq_automations` (automation on/off toggle) completely unchanged — unrelated to the thermometer swap.

## Design

### `packages/pkg_bbq.yaml`

Remove:
```yaml
input_number:
  grill_alert_low: ...
  grill_alert_high: ...
  grill_probe_2_target: ...
```

Replace the existing `template: sensor:` block (currently 2 entries keyed off `sensor.inkbird_ibt_2x_temperature_probe_1/2` and the removed `input_number`s) with 3 entries:

```yaml
template:
  - sensor:
    - default_entity_id: sensor.dome_alert_temp
      name: Dome Temp Alert
      state: >-
        {% if (states('sensor.tuin_bbq_dome_thermometer_ambient_temperature') | float(default=0)) < (states('number.tuin_bbq_dome_thermometer_ambient_minimum_temperature') | float(default=0)) or (states('sensor.tuin_bbq_dome_thermometer_ambient_temperature') | float(default=0)) > (states('number.tuin_bbq_dome_thermometer_ambient_maximum_temperature') | float(default=400)) %}
          Alert
        {% else %}
          Normal
        {% endif %}
    - default_entity_id: sensor.target_alert_temp_probe_1
      name: Probe 1 Target Alert
      state: >-
        {% if (states('sensor.probe_1_temperature') | float(default=0)) >= (states('number.probe_1_target_temperature') | float(default=250)) %}
          Alert
        {% else %}
          Normal
        {% endif %}
    - default_entity_id: sensor.target_alert_temp_probe_2
      name: Probe 2 Target Alert
      state: >-
        {% if (states('sensor.probe_2_temperature') | float(default=0)) >= (states('number.probe_2_target_temperature') | float(default=250)) %}
          Alert
        {% else %}
          Normal
        {% endif %}
```

`timer.bbq` and `input_boolean.enable_bbq_automations` stay exactly as they are today.

### `automations.yaml`

Rebuild the two existing BBQ alarm automations (aliased `BBQ - Probe 1 alarm` and `BBQ - Probe 2 alarm`, ids kept unchanged to preserve their entity registration) and add a third, all following the existing structure (condition on `input_boolean.enable_bbq_automations`, a per-automation cooldown via `last_triggered`, `notify.all_phones` + `script.sonos_say` actions):

1. **BBQ - Dome alarm** — trigger on `sensor.dome_alert_temp` == `Alert`; message reports `sensor.tuin_bbq_dome_thermometer_ambient_temperature`.
2. **BBQ - Probe 1 alarm** — trigger on `sensor.target_alert_temp_probe_1` == `Alert`; message reports `sensor.probe_1_temperature`.
3. **BBQ - Probe 2 alarm** — trigger on `sensor.target_alert_temp_probe_2` == `Alert`; message reports `sensor.probe_2_temperature`.

### `dashboards/popups/pp_bbq_garden.yaml`

- Temperature area becomes 3 columns instead of 2: Dome / Vlees 1 / Vlees 2, each a `gauge` (entity + alert `glance`) matching the existing visual pattern. Gauge ranges: dome `0–400`, both probes `0–250` (matching native entity ranges).
- "BBQ Targets" entities card: replace `input_number.grill_alert_low`/`grill_alert_high` rows with `number.tuin_bbq_dome_thermometer_ambient_minimum_temperature` / `_maximum_temperature`.
- "Vlees Targets" entities card: replace the single `input_number.grill_probe_2_target` row with two rows — `number.probe_1_target_temperature` ("Vlees 1") and `number.probe_2_target_temperature` ("Vlees 2").
- `mini-graph-card`: add a third series for `sensor.probe_2_temperature`.
- Kookwekker and Notificaties cards (timer, automation toggles) stay as-is, aside from updating the automation toggle rows to reference the (re)created automation entity IDs from the rebuilt automations above.

### Non-goals / explicitly out of scope

- No changes to `timer.bbq` or `input_boolean.enable_bbq_automations`.
- No removal of the physical Inkbird device's automations/entities beyond what's superseded here (if any other automation elsewhere references the Inkbird sensors, that's out of scope unless discovered during implementation, in which case it will be flagged before changing).
- No new notification channels or alert styles — same `notify.all_phones` + `script.sonos_say` pattern as today.

## Testing / Verification Plan

- Validate YAML syntax for all three changed files.
- Reload automations/templates via Home Assistant (template sensors and automations support hot reload, unlike the `history_stats` platform sensor from the earlier cat-tracking spec).
- Config-only verification: the physical ToGrill thermometer can't be powered on remotely, so live BLE readings can't be exercised in this session — confirm entity references resolve (no unknown-entity warnings) and the dashboard renders without card errors.
