# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About This Repository

Rob Sonke's personal Home Assistant configuration, shared publicly at
[robsonke/hass-config](https://github.com/robsonke/hass-config). The setup is Netherlands-based
(Amsterdam timezone) and covers a full smart home including lighting, heating (Daikin Altherma), pool,
solar, EV charging, alarm, presence tracking, and media.

## Working Agreements

- **Rob commits and pushes himself.** Never run `git commit`, `git add` or `git push`, and do not offer
  to. Leave finished work in the working tree and say what changed.
- **This directory is the live HA config.** Edits take effect on a running instance. There is no
  worktree to hide in — validate before reloading.
- **Reloads are fine to run; restarts are not.** Use the HA MCP for `homeassistant.reload_all`,
  `template.reload` and `shell_command.refresh_lovelace`. Ask before `homeassistant.restart`.

## Comment Style

Applies to every comment in this repo, in YAML and in ESPHome configs alike.

- **English only.** Entity friendly names, automation aliases and TTS text stay Dutch — comments do not.
- **Maximum 120 characters per line**, including indent and the `#`. Wrap onto more lines rather than
  cramming; `line-length` is disabled in yamllint, so this is a house rule, not a linter rule.
- **Two to three lines per block.** Say why something is the way it is, then stop.
- **Keep the reason, drop the story.** A measured value that justifies a threshold, a trap that will
  bite again, a constraint that is not visible in the code below: keep those. The build-up, the
  history, what was tried first, and anything readable straight from the code: cut.
- When a comment describes a character sequence that breaks Bubble Card (a backtick, a `${`, a Jinja
  delimiter), describe it in words instead of reproducing it — inside a `styles:` block the comment is
  evaluated too.

## Validation & CI

The GitHub Actions workflow (`.github/workflows/main.yml`) runs on push/PR:

1. **YAML Linting** via GitHub Super Linter — validates all YAML files (excludes `custom_components/`,
   `blueprints/`, `esphome/custom_components/`, `www/`, `.vscode/`)
2. **HA Config Check** via Frenck's HA action — validates `configuration.yaml` using fake secrets from
   `.stub/fakesecrets.yaml` against the stable HA release

To simulate CI locally, ensure your YAML is valid and that any secrets referenced in configs have
corresponding entries in `.stub/fakesecrets.yaml`.

`gitupdate.sh` exists for interactive commit + push, but Rob runs it — see Working Agreements.

## Architecture

### Configuration Entry Point
`configuration.yaml` is minimal — it loads packages and enables core integrations. Nearly all entity
definitions, automation triggers, and input helpers live in **packages**.

### Packages (`packages/`)
Feature-based YAML packages, each covering a domain: `pkg_lights.yaml`, `pkg_alarm.yaml`,
`pkg_pool.yaml`, `pkg_energy.yaml`, etc. This is where sensors, input helpers, template sensors, and
automation triggers are defined. When adding new entities or automations related to a feature area,
extend the relevant package file.

### Automations & Scripts
- `automations.yaml` — all automations; many use blueprints
- `scripts.yaml` — reusable scripts (Sonos TTS, light flash sequences, etc.)
- `blueprints/` — custom blueprints by robsonke plus community blueprints

### Dashboards (`dashboards/`)
Both dashboards are YAML-mode, registered in `configuration.yaml` under `lovelace:`:
- `bubble-dashboard.yaml` — the primary dashboard ("Home", in the sidebar)
- `backdoor-dashboard.yaml` — a small wall-tablet dashboard ("Bijkeuken", hidden from the sidebar)
- `dashboards/popups/` — 38 popup files, all named `bpp_*.yaml`, each `!include`d into
  `bubble-dashboard.yaml`

There is no `main-dashboard.yaml` — it was retired. Do not recreate it; `shell_command.refresh_lovelace`
in `pkg_system.yaml` used to `touch` it and would resurrect it as an empty file.

### Templates (`templates/`)
- `templates/decluttering_templates.yaml` — the only file here; decluttering card templates

The `templates/button_card_templates/` directory no longer exists. The dashboards were migrated off
`custom:button-card` template inheritance to Bubble Card.

### ESPHome (`esphome/`)
Device configs for Shelly Plug S power monitors, water meter, OnJu voice satellites, and pool
equipment. Shared settings live in `.common.yaml`. `esphome/archive/` holds retired device configs —
leave them alone unless asked.

### Custom Components (`custom_components/`)
30+ HACS/custom integrations. Notable ones: `alarmo`, `browser_mod`, `icloud3`, `frigate`, `powercalc`,
`nordpool`, `spook`, `pyscript`.

### AppDaemon (`appdaemon/apps/`)
ControllerX app for advanced controller/remote integration with Zigbee and other protocols.

### Themes (`themes/`)
Custom Frosted Glass theme (dark/light variants) plus community themes (Mushroom, iOS, Caule).

## Bubble Card

Cards are `custom:bubble-card`, on version 3.4.0. The split that matters:

- **Text belongs in `state_content:`** — plain YAML holding server-side Jinja. Every text label now uses
  it. The old trick of `show_state: true` plus a zero font-size on `.bubble-state` plus an `::after`
  rule whose `content` held a JS expression is fully migrated away, with none left. Do not reintroduce
  it.
- **Colour and layout belong in `styles:`** — client-side JS in `${ }` against `hass.states`, costing
  nothing server-side.

Both Jinja and `${ }` work inside a `styles:` block and can sit side by side; Bubble Card splits the
block into segments. Jinja there is worth it only when JS cannot express the thing, namely emitting or
omitting a whole CSS rule — a colour ternary gains nothing and costs a `render_template` subscription
per card per client. The three album-art blocks in `bubble-dashboard.yaml` are the standing example of
where it does pay off.

Traps, in order of how much time they cost:

- A Jinja block may **not enclose** a `${ }` span; Bubble Card warns about this in the browser console.
- Template detection is a plain substring scan for the Jinja delimiters, anywhere in the block —
  **including inside a CSS comment**. An accidental one still ships to the server.
- An **unbalanced** backtick ends the implicit template literal and silently kills the whole block. A
  matched pair delimiting a real nested JS template literal is fine and is in use today.
- Failures show up **only in the browser console**, never in the HA log. The in-app browser cannot
  reach the LAN, so live checks need Claude-in-Chrome.

Legacy state keys (`show_state`, `show_attribute`, `attribute`, `show_last_changed`) still work and are
deliberately kept on sub-buttons, where `show_attribute` gives unit-aware formatting that
`state_content` would lose.

## Key Patterns

- **Secrets**: All sensitive values (coordinates, API keys, URLs, passwords) are in `secrets.yaml`
  (git-ignored). Reference via `!secret key_name`.
- **Packages over inline config**: Prefer adding entities/automations to the appropriate
  `packages/pkg_*.yaml` rather than `configuration.yaml`.
- **Verify Jinja before it lands in YAML**: render it with `ha_eval_template` against live state first,
  including the failure paths (entity missing, attribute `none`, non-numeric state). `float` and `int`
  always take a default.
- **Popup pattern**: Each device/area has its own `bpp_*.yaml` in `dashboards/popups/`, using Bubble
  Card's native `card_type: pop-up` with a `hash:` key. They are opened by navigating to that hash
  (`tap_action: { action: navigate, navigation_path: '#pool' }`), **not** via `browser_mod` service
  calls — that migration is done. Only `bpp_stookalert.yaml` and `bpp_afval.yaml` still mention it.
- **Reloading YAML dashboards**: edits to `!include`d dashboard files are cached; use
  `shell_command.refresh_lovelace` to force HA to re-read them.
- **Group platforms need a restart to appear**: `binary_sensor: - platform: group` is legacy YAML
  platform config. `homeassistant.reload_all` picks up a changed member list on an existing group, but
  a newly added group only materialises after a restart.
- **Door and window groups**: `binary_sensor.doors_and_windows` is the outer shell and must stay exactly
  the union of `_downstairs`, `_upstairs` and `_garden`. `_downstairs` is exactly what Alarmo monitors
  downstairs. Interior doors live in `interior_doors_downstairs` and count towards none of it — they say
  nothing about whether the house is shut.
- **Dutch language**: Automation names, entity friendly names, and TTS scripts use Dutch (`nl`).
  Comments do not — see Comment Style.
