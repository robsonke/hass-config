# Bubble Card 3.4.0 — migratieplan dashboards

> **Voor agentic workers:** REQUIRED SUB-SKILL: gebruik superpowers:subagent-driven-development
> (aanbevolen) of superpowers:executing-plans om dit plan taak voor taak uit te voeren.
> Stappen gebruiken checkbox-syntax (`- [ ]`).

**Doel:** de CSS-hijack waarmee dit dashboard al zijn tekst rendert
(`show_state: true` + `.bubble-state { font-size: 0 }` + `::after { content: "${JS}" }`)
vervangen door het native `state_content` van Bubble Card 3.4.0, en de twee
apparaten die tot nu toe een native HA-kaart nodig hadden — de tapwatertank en de
luchtontvochtiger — omzetten naar `card_type: climate`.

**Aanpak:** per pop-up migreren, niet per optie. Tekst verhuist naar
`state_content` (server-side Jinja), kleur blijft in `styles:` (JS). Elke
migratie is los terug te draaien omdat de oude en nieuwe vorm niet naast elkaar
hoeven te bestaan.

**Tech stack:** Bubble Card 3.4.0, Home Assistant YAML-mode dashboards, Jinja2.

**Onderzoek:** deze sessie — releasenotes v3.4.0 plus een audit van 10.462 regels
dashboard-YAML. Kerncijfers: 161 JS-expressies die tekst produceren, 4 die een
icoon zetten, ~376 die echte CSS doen (die blijven).

## Globale randvoorwaarden

Gelden voor elke taak hieronder.

- **Niets breekt bij de upgrade.** `slide_to_close_distance`,
  `--bubble-sub-button-outline` en `--bubble-sub-slider-outline` komen 0× voor.
  De 124 legacy state-keys (`show_state`, `show_attribute`, `attribute`,
  `show_last_changed`) blijven in 3.4.0 gewoon werken; migreren mag op eigen tempo.
- **Geen automatische migratie.** Die draait alleen als een kaart in de
  GUI-editor geopend wordt. Dit zijn YAML-mode dashboards, dus dat gebeurt nooit.
- **Nieuwe val in 3.4.0:** elke `{{` of `{%` in een `styles:`-blok wordt nu naar
  de server gestuurd als Jinja — ook in een CSS-commentaar. Nu nog 0 gevallen;
  houd het zo. Dit komt bovenop de bestaande backtick-val (zie
  `bubble_card_template_literal_trap`): nooit backticks in Bubble-CSS of de
  commentaren daarin.
- **Houd `${ }` buiten `{% if %}`-blokken.** Een Jinja-blok dat een JS-span
  omsluit komt in twee helften bij de server aan en faalt.
- **Jinja alleen in de velden die het ondersteunen:** `name`, `icon`,
  `state_content`, sub-button `name`/`icon`, `<n>_name`/`<n>_icon`, `styles`, en
  `condition: template`. Níet in `entity`, `hash`, `card_type`, acties of
  numerieke opties.
- **Expliciete entity-id's in templates**, niet de `entity`-variabele. De
  variabele bestaat in 3.4.0, maar expliciete id's zijn met
  `ha_eval_template` vooraf te verifiëren. Pas de korte vorm toe als taak 1 en 2
  in de praktijk goed blijken.
- **Elk template eerst door `ha_eval_template`** voordat het in YAML belandt,
  inclusief de foutpaden (entity `unavailable`, attribuut `none`).
- **`float`/`int` altijd met default.** HA's filters gooien zonder default.
- **Rob commit zelf.** Geen enkele taak bevat een `git commit`.
- **Na elke YAML-wijziging `shell_command.refresh_lovelace`** — includes worden
  gecached (zie `yaml_dashboard_include_cache`).
- **Browserconsole is de enige plek waar een kapot styles-blok zichtbaar is.**
  Niet in het HA-log. Controleer via Claude-in-Chrome (de in-app browser komt
  niet op het LAN, zie `inapp_browser_no_lan`).

## Bestandsindeling

| Bestand | Verantwoordelijkheid in dit plan |
|---|---|
| `dashboards/popups/bpp_energy_dhw.yaml` | referentie-implementatie: 3 tekstmigraties + de tapwaterkaart |
| `dashboards/popups/bpp_climate_upstairs.yaml` | de luchtontvochtiger naar `card_type: climate` |
| `dashboards/popups/bpp_stookalert.yaml` | 4 imperatieve icoon-hacks naar `icon:` met Jinja |
| overige 35 `bpp_*.yaml` + `bubble-dashboard.yaml` | de resterende tekstmigraties, na evaluatie |

Volgorde is bewust: één pop-up volledig af als referentie, dan pas breedte.

## Evaluatiepunt

**Taak 1 en 2 zijn op 2026-09-19 uitgevoerd en live geverifieerd. Taak 3 en
verder zijn niet gestart en wachten op Robs beoordeling.**

Dat is het afgesproken kantelpunt: als de `state_content`-vorm in de praktijk
niet bevalt, is er 1 bestand teruggedraaid in plaats van 37.

---

### Taak 1: `bpp_energy_dhw.yaml` — referentie-implementatie

**Bestanden:**
- Wijzigen: `dashboards/popups/bpp_energy_dhw.yaml` (header 17-28, zonnesturing
  38-51, setpoint 55-67, tile-kaart 68-75)

**Levert op:** het patroon dat taak 3+ 161× herhaalt — tekst in `state_content`,
kleur in `styles:` op `.bubble-state` in plaats van `.bubble-state::after`.

- [x] **Stap 1: verifieer de drie templates tegen live state**

```
ha_eval_template met de drie templates uit stap 2/3/4, plus de foutpaden
(current_temperature = none, setpoint niet-numeriek).
```
Verwacht: `42°C · koelt af`, `aan`, `40° actief`, `48° ipv 52°`, `—`.

- [x] **Stap 2: header — vervang `show_state` + `::after` door `state_content`**

Verwijder `show_state: true` (regel 19) en zet:

```yaml
state_content: >-
  {%- set t = state_attr('water_heater.domestic_hot_water_tank','current_temperature') -%}
  {%- set p = states('sensor.dhw_phase') -%}
  {%- set label = {'opwarmen':'warmt op','afkoelen':'koelt af','ochtend':'ochtendvangnet','uit':'sturing uit'}.get(p, p) -%}
  {{ (t | round(0) | int ~ '°C') if t is not none else '—' }}{{ ' · ' ~ label if label else '' }}
```

In `styles:` vervalt de hele `.bubble-state::after`-regel; de kleur verhuist naar
`.bubble-state` zelf en `font-size: 0` gaat eruit:

```yaml
  .bubble-state { font-size: 14px !important; font-weight: 500; color: ${(() => { const p = hass.states['sensor.dhw_phase']?.state; return p === 'opwarmen' ? '#f0cf8f' : p === 'afkoelen' ? '#82bbf0' : p === 'ochtend' ? '#9ed9bd' : '#9b9aac'; })()} !important; }
```

De twee achtergrondregels (`.bubble-button-background`, `.bubble-icon-container`)
blijven ongewijzigd — dat is echte CSS.

- [x] **Stap 3: zonnesturing-knop**

Verwijder `button_type: state` niet, maar voeg toe:

```yaml
        state_content: "{{ 'aan' if is_state('input_boolean.dhw_solar_scheduling','on') else 'uit' }}"
```

en vervang in `styles:` de laatste regel door:

```yaml
          .bubble-state { font-size: 12.5px !important; color: ${state === 'on' ? '#f0cf8f' : '#8f8e9e'} !important; }
```

- [x] **Stap 4: setpoint-knop**

```yaml
        state_content: >-
          {%- set w = states('sensor.dhw_target_setpoint') | float(-999) -%}
          {%- set a = state_attr('water_heater.domestic_hot_water_tank','temperature') | float(-999) -%}
          {%- if w == -999 or a == -999 -%}—
          {%- elif (w - a) | abs >= 0.5 -%}{{ a | round(0) | int }}° ipv {{ w | round(0) | int }}°
          {%- else -%}{{ w | round(0) | int }}° actief
          {%- endif -%}
```

en in `styles:` de `::after` vervangen door `.bubble-state` met dezelfde
drift-kleurlogica die er al staat.

- [x] **Stap 5: tapwaterkaart — `type: tile` wordt `card_type: climate`**

Vervang regels 68-75 door:

```yaml
  - type: custom:bubble-card
    card_type: climate
    entity: water_heater.domestic_hot_water_tank
    name: Tapwater
    icon: mdi:water-boiler
    state_color: false
    sub_button:
      - select_attribute: operation_list
        state_background: false
```

`state_color: false` en het ontbreken van `name:` / `show_arrow:` op de
sub-button zijn uitkomsten van de eerste render — zie de bevindingen onderaan.

`min_temp`/`max_temp` bewust weggelaten: de kaart leest ze van de entiteit
(nu 30-55), zodat een gewijzigde veldinstelling op de unit vanzelf doorwerkt.

**Let op — bewuste gedragswijziging.** De `tile` toonde alléén de
operation-modes. De climate-kaart zet daar een setpoint-schuif naast. De
DHW-reconciler bezit dat setpoint en schrijft het elke 10 minuten terug, dus
handmatig schuiven houdt hooguit één cyclus stand. Dat is niet gevaarlijk, maar
het is wel nieuwe UI die tegen de automation in werkt. Alternatief als dat
stoort: `card_type: button` met alleen een modus-sub-button.

- [x] **Stap 6: verifieer**

```bash
python3 -c "import yaml,sys; yaml.safe_load(open('dashboards/popups/bpp_energy_dhw.yaml'))" && echo OK
```
Daarna `shell_command.refresh_lovelace` via de HA MCP, `#warm-water` openen in
Chrome, en de console controleren op `Bubble Card - Template Error`.
Verwacht: geen enkele Bubble-regel in de console, en de kop leest `42°C · koelt af`.

---

### Taak 2: luchtontvochtiger naar `card_type: climate`

**Bestanden:**
- Wijzigen: `dashboards/popups/bpp_climate_upstairs.yaml` (de `type: humidifier`-kaart)

**Levert op:** de laatste native HA-kaart in deze pop-up verdwijnt.

- [x] **Stap 1: vervang de native humidifier-kaart**

```yaml
  - type: custom:bubble-card
    card_type: climate
    entity: humidifier.master_bedroom
    name: Luchtontvochtiger
    icon: mdi:air-humidifier
    state_color: true
    sub_button:
      - name: Modus
        select_attribute: available_modes
        show_arrow: false
        state_background: false
```

`available_modes` is het humidifier-equivalent van `hvac_modes`; de entiteit
levert `[Set, Smart, Continuous, Dry]` — exact de vier die de oude kaart
hardcodeerde, dus die lijst hoeft niet meer in de YAML.
`device_class: dehumidifier` betekent dat de kleur uit
`--bubble-state-humidifier-dehumidifier-on-color` komt.

**Let op:** `min_temp`/`max_temp`/`step` zijn op een humidifier
*vochtigheids*waarden ondanks de namen. Weggelaten, dus de kaart leest
`min_humidity: 35` / `max_humidity: 85` van de entiteit.

- [x] **Stap 2: verifieer**

De entiteit staat nu `unavailable`, dus visuele controle is beperkt tot de
onbeschikbaar-weergave. YAML-parse en console moeten wel schoon zijn.

---

## Na de evaluatie — taak 3 en verder

Niet uitvoeren voordat Rob taak 1 en 2 beoordeeld heeft.

### Taak 3: `bpp_stookalert.yaml` — 4 icoon-hacks

Regels 53, 78, 103, 128 muteren de DOM om een sub-button-icoon te zetten:

```yaml
${subButtonIcon[0].setAttribute("icon", hass.states[entity].attributes['definitive'] === true ? 'mdi:lock' : '')}
```

wordt op de sub-button zelf:

```yaml
        icon: "{{ 'mdi:lock' if state_attr('binary_sensor.<id>','definitive') else '' }}"
```

Dit bestand heeft ook de dichtste cluster legacy-keys (9× `show_state`,
9× `show_attribute`, 5× `show_last_changed`, 4× `attribute: time`) — in dezelfde
beurt meenemen.

### Taak 4-N: de resterende tekstmigraties

Per bestand, aflopend op aantal tekst-producerende JS-expressies:

| Bestand | Tekst-JS |
|---|---|
| `bubble-dashboard.yaml` | 20 |
| `bpp_doors_downstairs.yaml` | 14 |
| `bpp_music_hub.yaml` | 8 |
| `bpp_irrigation_garden.yaml` | 8 |
| `bpp_energy_usage.yaml` | 8 |
| `bpp_strava.yaml` / `bpp_strava_steffi.yaml` | 7 elk |
| `bpp_car_ix3.yaml` | 7 |
| overige 28 bestanden | 1-6 elk |

Terugkerende idiomen die in Jinja korter zijn: Nederlandse decimale komma
(`| round(2) | string | replace('.', ',')`), relatieve leeftijd
(`relative_time(states.x.last_changed)`), en groepsleden tellen
(`expand('light.lights_downstairs') | selectattr('state','eq','on') | list | count`).

**Niet aanraken:**
- `bubble_card/modules/bubble_weather.yaml` — betaalde, niet-OSS module van
  Clooos. Bevat 6 `show_state`, 4 `show_attribute`, 6 `show_last_changed`; laat
  zijn eigen update dat doen.
- De ~376 JS-expressies voor kleur, gradient, glow en animatie.
- `popup_style: home-assistant` — forceert `adaptive-dialog` en de HA
  more-info-header; botst met het Frosted Glass-uiterlijk.

### Taak N+1: media-player-kaarten evalueren

`card_type: media-player` is niet nieuw in 3.4.0, maar toont sinds 3.4.0 wél wat
er speelt (serie + aflevering, radiozender, playlist, app-naam) in plaats van
terug te vallen op de kaartnaam. Er zijn nu 0 Bubble media-player-kaarten; alle
14 Sonos-plekken zijn `card_type: button` met handgeschreven now-playing-tekst.

**Blokkade om eerst op te lossen:** in `bpp_music_hub.yaml` overschrijven de
`name:`-velden bewust de friendly names (`office_ma_sonos` → "Shed",
`unnamed_room_3` → "Office", `unnamed_room` → "Eva"). Een kaarttype dat de naam
door de now-playing-tekst vervangt verliest die. Overweeg eerst de entiteiten te
hernoemen in het register (zie `energy_card_labels_from_friendly_name`).

---

## Bevindingen uit taak 1 en 2 (2026-09-19)

Wat de referentie-implementatie opleverde, voor wie taak 3+ oppakt:

1. **`state_color: true` op een water_heater is te fel.** De aan-kleur is
   verzadigd geel en vecht met de ingetogen rgba-tinten van deze dashboards.
   Op `false` gezet; de fase-kleur staat al in de kop van de pop-up.
2. **De climate-kaart voegt een setpoint-schuif toe die de `tile` niet had.**
   De DHW-reconciler schrijft het setpoint elke 10 minuten terug, dus handmatig
   schuiven houdt hooguit één cyclus stand. Niet gevaarlijk, wel nieuwe UI die
   tegen de automation in werkt. Laten staan tot Rob er iets van vindt.
3. **Een `select_attribute`-sub-button toont de huidige waarde, niet `name:`.**
   `name: Modus` werd niet gerenderd; zonder `name` en zonder
   `show_arrow: false` krijg je een herkenbare dropdown met pijl. Zo gelaten.
4. **Kleur-CSS verhuist van `.bubble-state::after` naar `.bubble-state`** en
   `font-size: 0` moet weg. Vergeet dat laatste niet: anders is de tekst er wel
   maar onzichtbaar.
5. **Chrome serveert na een HACS-update een verouderde service worker.** De
   eerste laadpoging faalde met `Failed to fetch dynamically imported module`.
   Een harde herlaad (cmd+shift+R) loste het op. Niet verwarren met een kapotte
   kaart — dit heeft niets met de YAML te maken.
6. **Verificatie die werkt:** `ha_eval_template` vooraf per template (inclusief
   foutpaden), daarna `shell_command.refresh_lovelace`, harde herlaad, en de
   browserconsole filteren op `Bubble|Template|Jinja`. Schoon resultaat is
   uitsluitend de `Bubble Card v3.4.0`-infobanner.
