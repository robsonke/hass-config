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
- `main-dashboard.yaml` — primary Lovelace dashboard
- `dashboards/popups/` — 26+ modular popup views (one per device/feature area), used with `browser_mod` for overlay popups

### Templates (`templates/`)
- `templates/button_card_templates/` — reusable `custom:button-card` templates (`tpl_main.yaml`, `tpl_base.yaml`, etc.)
- `templates/decluttering_templates.yaml` — decluttering card templates

All dashboard cards inherit from these templates for visual consistency. When editing popups, check `tpl_main.yaml` for shared styles and variables.

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
- **Template-driven UI**: Dashboard cards use `custom:button-card` with template inheritance. Avoid hardcoding styles in individual popup files.
- **Popup pattern**: Each device/area has its own popup YAML in `dashboards/popups/`. Popups are triggered via `browser_mod` service calls.
- **Dutch language**: Automation names, entity friendly names, and TTS scripts use Dutch (`nl`).
