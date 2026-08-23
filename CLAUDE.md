# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About This Repository

Rob Sonke's personal Home Assistant configuration, shared publicly at [robsonke/hass-config](https://github.com/robsonke/hass-config). The setup is Netherlands-based (Amsterdam timezone) and covers a full smart home including lighting, heating (Daikin Altherma), pool, solar, EV charging, alarm, presence tracking, and media.

## Validation & CI

The GitHub Actions workflow (`.github/workflows/main.yml`) runs on push/PR:

1. **YAML Linting** via GitHub Super Linter — validates all YAML files (excludes `custom_components/`, `blueprints/`, `esphome/custom_components/`, `www/`, `.vscode/`)
2. **HA Config Check** via Frenck's HA action — validates `configuration.yaml` using fake secrets from `.stub/fakesecrets.yaml` against the stable HA release

To simulate CI locally, ensure your YAML is valid and that any secrets referenced in configs have corresponding entries in `.stub/fakesecrets.yaml`.

## Committing Changes

Use `gitupdate.sh` for interactive commit + push:
```bash
./gitupdate.sh
```
It runs `git add .`, shows status, prompts for a commit message (default: "Minor Updates"), then pushes to `origin/master`.

## Architecture

### Configuration Entry Point
`configuration.yaml` is minimal — it loads packages and enables core integrations. Nearly all entity definitions, automations triggers, and input helpers live in **packages**.

### Packages (`packages/`)
Feature-based YAML packages, each covering a domain: `pkg_lights.yaml`, `pkg_alarm.yaml`, `pkg_pool.yaml`, `pkg_energy.yaml`, etc. This is where sensors, input helpers, template sensors, and automation triggers are defined. When adding new entities or automations related to a feature area, extend the relevant package file.

### Automations & Scripts
- `automations.yaml` — all automations (3700+ lines); many use blueprints
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
`custom:button-card` template inheritance to Bubble Card, so there is no shared `tpl_main.yaml` to
consult — styling now lives per-card in the `styles:` block of each Bubble Card.

### ESPHome (`esphome/`)
Device configs for Shelly Plug S power monitors, water meter, OnJu voice satellites, and pool equipment. Shared settings live in `.common.yaml`.

### Custom Components (`custom_components/`)
30+ HACS/custom integrations. Notable ones: `alarmo`, `browser_mod`, `icloud3`, `frigate`, `powercalc`, `nordpool`, `spook`, `pyscript`.

### AppDaemon (`appdaemon/apps/`)
ControllerX app for advanced controller/remote integration with Zigbee and other protocols.

### Themes (`themes/`)
Custom Frosted Glass theme (dark/light variants) plus community themes (Mushroom, iOS, Caule).

## Key Patterns

- **Secrets**: All sensitive values (coordinates, API keys, URLs, passwords) are in `secrets.yaml` (git-ignored). Reference via `!secret key_name`.
- **Packages over inline config**: Prefer adding entities/automations to the appropriate `packages/pkg_*.yaml` rather than `configuration.yaml`.
- **Bubble Card UI**: Cards are `custom:bubble-card`. Styling goes in each card's own `styles:` block
  (JS template literals against `hass.states`). Beware: a backtick anywhere inside a Bubble Card
  `styles:` or `modules:` block — including in a comment — silently kills the entire block.
- **Popup pattern**: Each device/area has its own `bpp_*.yaml` in `dashboards/popups/`, using Bubble
  Card's native `card_type: pop-up` with a `hash:` key. They are opened by navigating to that hash
  (`tap_action: { action: navigate, navigation_path: '#pool' }`), **not** via `browser_mod` service
  calls — that migration is done. Only two files still reference `browser_mod` at all.
- **Reloading YAML dashboards**: edits to `!include`d dashboard files are cached; use
  `shell_command.refresh_lovelace` to force HA to re-read them.
- **Dutch language**: Automation names, entity friendly names, and TTS scripts use Dutch (`nl`).
