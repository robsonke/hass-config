# Bijkeuken Cat Camera Sighting Tracker

Date: 2026-07-05
File: `packages/pkg_persons.yaml`

## Problem

The user wants to track how often a cat is spotted by Frigate's object detection on the `bijkeuken` (utility room) camera, as a first step toward a future dashboard popup showing "when a cat was seen" plus a range of Frigate snapshots. This spec covers only the tracking/counting piece; the dashboard popup itself is explicitly deferred to a later task.

Investigation found that cat detection already exists and needs no new setup:

- `binary_sensor.bijkeuken_cat_occupancy` — Frigate's cat-occupancy sensor for this camera, already live.
- `image.bijkeuken_cat` — Frigate's auto-updating "best snapshot" image entity for the most recent cat detection.
- Frigate itself retains its own event history (with snapshots/clips) per camera/label, independent of Home Assistant.
- `packages/pkg_persons.yaml:47-54` already contains the exact pattern needed, for a different sensor: `sensor.cat_door_today`, a `history_stats` sensor counting `on` transitions of `binary_sensor.motion_sensor_cats_occupancy` since midnight (the physical cat-flap sensor, unrelated to the camera).

## Goals

1. Count cat sightings via the bijkeuken camera, resetting at midnight (matching the existing `cat_door_today` convention, not a rolling 24h window).
2. No new automation, notification, or custom storage — reuse native Home Assistant mechanisms wherever one already exists.
3. Leave "collecting occurrences" (timestamps of each sighting) to Home Assistant's built-in Logbook, which already timestamps every state transition of `binary_sensor.bijkeuken_cat_occupancy` with no extra configuration.
4. Leave snapshot handling to Frigate's own event history and the existing `image.bijkeuken_cat` entity — no new snapshot storage.
5. No dashboard changes in this spec — the "cats" button-card template in `dashboards/main-dashboard.yaml` is untouched for now.

## Design

Add one `history_stats` sensor to the existing `sensor:` block in `packages/pkg_persons.yaml`, directly below `cat_door_today`, mirroring its structure exactly:

```yaml
  - platform: history_stats
    name: Bijkeuken cat sightings today
    entity_id: binary_sensor.bijkeuken_cat_occupancy
    state: "on"
    type: count
    start: "{{ now().replace(hour=0, minute=0, second=0) }}"
    end: "{{ now() }}"
```

Resulting entity: `sensor.bijkeuken_cat_sightings_today`. It counts how many times `binary_sensor.bijkeuken_cat_occupancy` has turned `on` since midnight, and naturally resets to 0 each day because `start` is recalculated on every evaluation — no counter, timer, or reset automation required.

### Non-goals / explicitly out of scope

- No dashboard/popup changes (future task).
- No notifications on cat sighting.
- No custom sighting log/list entity — the Logbook already provides this.
- No changes to Frigate's own configuration (cat detection already works).

## Testing / Verification Plan

- Validate YAML syntax.
- Reload/restart Home Assistant core config so the new `history_stats` sensor registers.
- Confirm `sensor.bijkeuken_cat_sightings_today` appears and its state matches the number of `binary_sensor.bijkeuken_cat_occupancy` "on" transitions logged since midnight (cross-check against Logbook history for that entity).
