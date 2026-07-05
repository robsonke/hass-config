# Eva Bed Sound Detection — Redesign

Date: 2026-07-05
Automation: `automations.yaml` — `evabed_sound_detection_armed_night` (id: `eva_bed_sound_detection_armed_night`)

## Problem

The existing automation triggers on a generic Home Assistant `frigate_events` event with `event_data: {type: sound, camera: evabed}`. This is a blunt, unclassified signal — it doesn't distinguish crying from coughing from ambient noise, and doesn't account for whether a sound is a one-off blip or a sustained episode. In practice it "doesn't work well" per the owner.

Investigation of the live Home Assistant instance found that Frigate's audio classification is already running for the `evabed` camera and exposes dedicated per-sound binary sensors:

- `binary_sensor.evabed_crying_sound`
- `binary_sensor.evabed_cough_sound`
- `binary_sensor.evabed_scream_sound`
- `binary_sensor.evabed_yell_sound`
- `binary_sensor.evabed_snoring_sound` (excluded — normal sleep noise)

30 days of history showed these sensors pulse `on` → `off` in short (~30s) bursts, even during what is presumably one continuous episode (e.g., `snoring_sound` toggled on/off three times between 07:04–07:08 on 2026-06-25). This means a naive `for: 1 minute` state condition cannot detect "sustained" sound — sustained behavior must be inferred from multiple pulses recurring with short gaps, not one long `on` state.

## Goals

1. Use the classified sensors instead of the generic event, restricted to actual distress/unusual sounds: crying, screaming, yelling, coughing. Snoring is excluded.
2. Two-tier alerting:
   - **Tier 1 (first detection):** normal-priority push notification, sent immediately.
   - **Tier 2 (sustained):** if the sound recurs at least 2 more times, each within 2 minutes of the previous detection (3 total), escalate to a critical/persistent push — same urgency as today's notification.
3. Avoid notification spam during one ongoing episode; apply a 5-minute cooldown before a new episode can alert again.
4. Attach a camera snapshot to both notification tiers so the recipient can see context without opening the app.
5. Keep scope limited to `armed_night` (no change to when the automation is active).

## Design

### Trigger

State trigger, `to: "on"`, on:
- `binary_sensor.evabed_crying_sound`
- `binary_sensor.evabed_scream_sound`
- `binary_sensor.evabed_yell_sound`
- `binary_sensor.evabed_cough_sound`

### Conditions (gate before running)

1. `alarm_control_panel.alarmo` state is `armed_night`.
2. Cooldown: `{{ as_timestamp(now()) - as_timestamp(states.automation.eva_bed_sound_detection_armed_night.attributes.last_triggered, 0) | int > 300 }}` — mirrors the existing cooldown idiom already used in `presence_frigate_object_detection` elsewhere in `automations.yaml`, for consistency.

### Action flow (no new helper entities)

1. Take a snapshot: `camera.snapshot` on `camera.evabed` → `/config/www/screenshots/evabed_sound.jpg` (reuses the existing `www/screenshots/` directory rather than creating a new one).
2. Send Tier 1 notification via `notify.all_phones`:
   - Title: "🔊 Geluid bij Eva"
   - Message: "Eva maakt geluid ({{ sound label }})" where the sound label is derived from `trigger.entity_id` via a fixed Dutch mapping: `evabed_crying_sound` → "huilen", `evabed_scream_sound` → "gillen", `evabed_yell_sound` → "schreeuwen", `evabed_cough_sound` → "hoesten".
   - `data.image`: `http://192.168.0.40:8123/local/screenshots/evabed_sound.jpg?t={{ now().timestamp() }}` (cache-busted, matching the existing image-attachment pattern used elsewhere in this file)
   - `data.persistent: true`, `data.tag: eva-sound`
   - Normal push priority (no `critical` override).
3. `repeat: count: 2`, sequence per iteration:
   - `wait_for_trigger`: same 4-sensor state trigger (`to: "on"`), `timeout: "00:02:00"`.
   - `if: "{{ wait.trigger is none }}"` (timed out — no further sound) → `stop:` ends the automation run here. No escalation.
   - Otherwise the loop continues to the next iteration.
4. If the repeat completes both iterations without timing out (i.e., 2 more detections arrived, each within 2 minutes of the last — 3 total), send the Tier 2 escalation notification via `notify.all_phones`:
   - Title: "⚠️ Aanhoudend geluid bij Eva"
   - Message: "Eva maakt al even geluid, ga even kijken!"
   - Same snapshot/image attachment (re-snapshotted, or reuse step 1's if not re-taken — implementation will re-snapshot for freshness).
   - `data.persistent: true`, `data.tag: eva-sound`, critical push: `push.sound.critical: 1`, `push.interruption-level: critical` (matches today's existing critical-alert behavior).

### Why this needs no new helpers

The `repeat` + `wait_for_trigger` + `stop` combination lets a single automation run track "has this recurred enough, closely enough together" purely with native automation actions — no `counter`/`timer` helper entities required. The automation's default `mode: single` also means new trigger firings while a session is already active (i.e., during the up-to-~4-minute repeat/wait window) don't spawn concurrent runs; they're instead picked up by the running instance's `wait_for_trigger`.

### Non-goals / explicitly out of scope

- No change to when the automation is active (armed_night only — no daytime nap coverage).
- No new input_boolean/counter/timer helpers.
- No changes to the Frigate audio-classification configuration itself (it's already working correctly).

## Testing / Verification Plan

- Validate YAML syntax (matches repo's YAML lint CI check).
- Confirm the new automation ID keeps the same `id:` field so it doesn't create a duplicate automation entity in the HA registry.
- Manually verify via Home Assistant that `camera.snapshot` can write to `/config/www/screenshots/` (directory already exists, used by `main-dashboard.jpg`).
- Where possible, simulate by manually toggling the binary sensors (e.g., via Developer Tools) to confirm tier-1 fires immediately and tier-2 fires only after 3 detections within the gap window, and that the cooldown suppresses immediate re-firing.
