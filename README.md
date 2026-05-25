# Connection Observer

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/OleSint/ha-connection-observer)](https://github.com/OleSint/ha-connection-observer/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

📖 **[English](docs/DOCUMENTATION.md)** · **[Deutsch](docs/DOKUMENTATION.md)** · **[Français](docs/DOCUMENTATION_FR.md)** · **[Nederlands](docs/DOCUMENTATION_NL.md)** · **[Español](docs/DOCUMENTATION_ES.md)**

> **Deutsch weiter unten** ↓

---

## English

**Connection Observer** monitors your smart home devices and alerts you when they lose their connection — before you notice a stuck light switch or a missing sensor reading.

### Features

- **Protocol-based monitoring** – select entire integration families (Zigbee, Z-Wave, Hue, ESPHome, Shelly, Sonos, …) instead of configuring individual entities. 100+ integrations supported out of the box.
- **Immediate notifications** – get alerted the moment a device goes offline
- **Scheduled summaries** – receive a digest on configurable days and times listing everything that disconnected since the last summary, including whether the device came back online and when
- **Both modes simultaneously** – immediate + summary can both be active at once; summary is pre-selected by default
- **Reconnect notifications** – opt-in alert when a device comes back online
- **Alert delay** – opt-in: only create an event after a device has been offline for N minutes, filtering out brief dropouts entirely
- **Cooldown** – opt-in: limit immediate notifications per device to once every N minutes
- **Minimum offline duration** – opt-in: suppress short blips from the summary without losing them
- **Room / area** – opt-in: include the HA area name in notifications
- **Manufacturer & model** – opt-in: include device info in immediate notifications
- **Per-entity exclusions** – exclude specific noisy entities from monitoring
- **Domain exclusions** – exclude entire entity domains (e.g. `sensor`, `button`) from monitoring; `device_tracker` is always excluded automatically
- **Per-protocol alert delays** *(v1.1.0)* – set individual alert delays per integration family; use "Apply recommended delays" for a one-click starting point
- **Watch label – custom offline indicators** *(v1.1.0)* – label any HA entity (e.g. a template binary sensor) to monitor devices that never go `unavailable`, such as passive BLE sensors (BTHome, GARDENA Bluetooth)
- **Test notification in options** – re-send a test notification any time you change your notification services
- **5 languages** – notification messages in English, German, French, Dutch, or Spanish (configurable)
- **Notification templates** – customise the text of any notification with your own format string; variables like `{device_name}`, `{protocol}`, and `{time}` are available
- **HA Repairs integration** – after a configurable number of hours offline, an issue appears in Home Assistant's built-in Repairs panel; resolved automatically when the device comes back
- **Test notification** – built-in test step during setup to verify your notification service works
- **Persistent state** – events survive Home Assistant restarts; an HA restart itself never triggers a false disconnect alarm
- **Watchdog** – runs silently every 5 minutes to catch reconnects that did not produce a state-change event

### Entities

| Entity | Type | Description |
|---|---|---|
| `sensor.connection_observer_offline_devices` | Sensor | Number of devices currently offline. Attribute `devices` lists their names. |
| `sensor.connection_observer_pending_summary_events` | Sensor | Number of events not yet included in a summary. |
| `binary_sensor.connection_observer_connection_problem` | Binary Sensor | `ON` = at least one device is offline. Use in automations or dashboards. |

### Services

| Service | Description |
|---|---|
| `connection_observer.send_summary_now` | Immediately send a summary of all pending events, without waiting for the next scheduled time. |
| `connection_observer.clear_history` | Clear all stored disconnect events. Resets the pending-events sensor to 0. |
| `connection_observer.clear_device` | Remove all stored events for a specific device (pass any entity of that device). Also resolves any open HA Repairs issue for it. |

### How it works

Connection Observer listens for entities transitioning to the `unavailable` state — the standard Home Assistant mechanism used by virtually all integrations when a device can no longer be reached. When a device with multiple entities goes offline, only **one** notification is sent per device (not one per entity).

The built-in watchdog runs every 5 minutes and catches any reconnects that did not produce a `state_changed` event, keeping the offline count accurate at all times.

Only integrations that are actually configured in your HA instance appear as options during setup.

### Installation

#### Via HACS (recommended)

1. Open **HACS → Integrations**
2. Click the three-dot menu → **Custom repositories**
3. Add `https://github.com/OleSint/ha-connection-observer` as type **Integration**
4. Search for **Connection Observer** and install it
5. Restart Home Assistant

#### Manual

1. Copy the `custom_components/connection_observer` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant

### Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Connection Observer**
3. **Step 1 – Protocols**: Select the integration families to monitor and choose your notification language
4. **Step 2 – Notifications**: Select one or more notification services; configure immediate and/or summary notifications
5. **Step 3 – Test**: Optionally send a test notification to verify your setup
6. **Step 4 – Advanced** *(all optional, 0 = disabled)*:
   - Alert delay, cooldown, minimum offline duration
   - Room/area and device info in notifications
   - Excluded entities

All settings — plus notification templates and the HA Repairs threshold — can be changed later via the **Configure** button on the integration card.

### Notification examples

**Immediate (English) — with area and device info enabled:**
> ⚠️ Living Room Plug (shelly) lost connection at 14:32.
> 📍 Living Room  ·  Shelly Plus 1PM

**Summary (English):**
> 📋 3 device(s) affected since last summary:
> • Kitchen Sensor [Kitchen] (zha): offline since 05/12 07:15, back online at 07:42
> • Bedroom Bulb [Bedroom] (hue): offline since 05/12 09:05 ⚠️ still offline
> • Hallway Motion (esphome): offline since 05/12 11:20, back online at 11:28

### Requirements

- Home Assistant 2023.6 or newer
- At least one supported integration configured

---

## Deutsch

**Connection Observer** überwacht deine Smart-Home-Geräte und benachrichtigt dich, wenn die Verbindung abbricht — bevor du selbst merkst, dass ein Lichtschalter nicht mehr reagiert oder ein Sensor keine Werte mehr liefert.

### Funktionen

- **Protokollbasierte Überwachung** – ganze Integrationsfamilien auswählen (Zigbee, Z-Wave, Hue, ESPHome, Shelly, Sonos, …) statt einzelner Entitäten. Über 100 Integrationen werden unterstützt.
- **Domänen ausschließen** – ganze Entitätsdomänen von der Überwachung ausnehmen (z. B. `sensor`, `button`); `device_tracker` wird immer automatisch ignoriert
- **Test im Options-Flow** – Testbenachrichtigung jederzeit neu senden, auch nach der Ersteinrichtung
- **Sofortbenachrichtigung** – wird direkt gesendet, sobald ein Gerät offline geht
- **Geplante Zusammenfassung** – Sammelnachricht zu konfigurierbaren Tagen und Uhrzeiten mit allen Verbindungsabbrüchen seit der letzten Zusammenfassung
- **Beide Modi gleichzeitig** – Sofort + Zusammenfassung können parallel aktiv sein; Zusammenfassung ist standardmäßig vorausgewählt
- **Wiederverbindungsbenachrichtigung** – optionale Meldung, wenn ein Gerät wieder online geht
- **Verzögerung** – opt-in: Ereignis wird erst erstellt, wenn das Gerät N Minuten offline war — kurze Aussetzer werden komplett ignoriert
- **Cooldown** – opt-in: Sofortbenachrichtigung pro Gerät höchstens alle N Minuten
- **Mindestausfallzeit** – opt-in: kurze Aussetzer werden aus der Zusammenfassung herausgefiltert
- **Raum / Bereich** – opt-in: HA-Bereichsname in Benachrichtigungen einblenden
- **Hersteller & Modell** – opt-in: Geräteinformationen in Sofortmeldungen einblenden
- **Entitäten ausschließen** – einzelne, störungsanfällige Entitäten von der Überwachung ausnehmen
- **5 Sprachen** – Benachrichtigungen auf Englisch, Deutsch, Französisch, Niederländisch oder Spanisch (konfigurierbar)
- **Benachrichtigungsvorlagen** – Texte beliebig anpassen mit Variablen wie `{device_name}`, `{protocol}` und `{time}`
- **HA-Reparaturen** – nach einer konfigurierbaren Offline-Dauer erscheint ein Eintrag im HA Repairs-Panel; wird automatisch gelöst, wenn das Gerät zurückkommt
- **Protokollspezifische Verzögerungen** *(v1.1.0)* – individuelle Verzögerung pro Integrationsfamilie; mit „Empfohlene Verzögerungen anwenden" im Experten-Schritt per Klick vorkonfigurieren
- **Watch-Label – eigene Offline-Indikatoren** *(v1.1.0)* – beliebige HA-Entität (z. B. ein Template-Binärsensor) mit einem Label versehen, um Geräte zu überwachen, die nie `unavailable` werden — ideal für passive BLE-Sensoren (BTHome, GARDENA Bluetooth)
- **Testbenachrichtigung** – integrierter Testschritt im Setup-Assistenten
- **Persistenter Zustand** – Ereignisse überleben HA-Neustarts; ein Neustart löst keinen falschen Alarm aus
- **Watchdog** – läuft alle 5 Minuten still im Hintergrund und fängt Reconnects ab, die kein State-Change-Event ausgelöst haben

### Entitäten

| Entität | Typ | Beschreibung |
|---|---|---|
| `sensor.connection_observer_offline_devices` | Sensor | Anzahl aktuell offline befindlicher Geräte. Attribut `devices` listet die Namen. |
| `sensor.connection_observer_pending_summary_events` | Sensor | Anzahl der Ereignisse, die noch nicht in einer Zusammenfassung waren. |
| `binary_sensor.connection_observer_connection_problem` | Binary Sensor | `EIN` = mindestens ein Gerät ist offline. Ideal für Automationen und Dashboards. |

### Services

| Service | Beschreibung |
|---|---|
| `connection_observer.send_summary_now` | Zusammenfassung sofort senden, ohne auf den nächsten geplanten Zeitpunkt zu warten. |
| `connection_observer.clear_history` | Alle gespeicherten Ereignisse löschen. Setzt den Pending-Sensor auf 0 zurück. |
| `connection_observer.clear_device` | Alle gespeicherten Ereignisse für ein bestimmtes Gerät löschen (beliebige Entität des Geräts angeben). Löst auch einen offenen HA-Reparatureintrag auf. |

### Funktionsprinzip

Connection Observer überwacht, wann Entitäten den Status `unavailable` annehmen — der Standard-Mechanismus in HA, den nahezu alle Integrationen verwenden, wenn ein Gerät nicht mehr erreichbar ist. Hat ein Gerät mehrere Entitäten, wird nur **eine** Benachrichtigung pro Gerät ausgelöst.

Der integrierte Watchdog läuft alle 5 Minuten und fängt Reconnects ab, die kein `state_changed`-Event ausgelöst haben, damit der Offline-Zähler immer korrekt bleibt.

Im Setup-Assistenten erscheinen nur Integrationen, die in der jeweiligen HA-Instanz auch wirklich konfiguriert sind.

### Installation

#### Über HACS (empfohlen)

1. **HACS → Integrationen** öffnen
2. Drei-Punkte-Menü → **Benutzerdefinierte Repositories**
3. `https://github.com/OleSint/ha-connection-observer` als **Integration** hinzufügen
4. Nach **Connection Observer** suchen und installieren
5. Home Assistant neu starten

#### Manuell

1. Den Ordner `custom_components/connection_observer` in `config/custom_components/` kopieren
2. Home Assistant neu starten

### Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach **Connection Observer** suchen
3. **Schritt 1 – Protokolle**: Zu überwachende Integrationsfamilien und Benachrichtigungssprache auswählen
4. **Schritt 2 – Benachrichtigungen**: Einen oder mehrere Dienste auswählen; Sofort- und/oder Zusammenfassungsmodus konfigurieren
5. **Schritt 3 – Test**: Optional eine Testbenachrichtigung senden
6. **Schritt 4 – Erweitert** *(alle Felder optional, 0 = deaktiviert)*:
   - Verzögerung, Cooldown, Mindestausfallzeit
   - Raum/Bereich und Geräteinformationen in Benachrichtigungen
   - Ausgeschlossene Entitäten
7. **Schritt 5 – Experte** *(optional)*:
   - Protokollspezifische Verzögerungen (oder „Empfohlene Verzögerungen anwenden")
   - Watch-Label für benutzerdefinierte Offline-Indikatoren

Alle Einstellungen — sowie Benachrichtigungsvorlagen und der HA-Reparaturen-Schwellwert — können nachträglich über den **Konfigurieren**-Button der Integrationskarte geändert werden.

### Beispiel-Benachrichtigungen

**Sofort (Deutsch) — mit Raum und Geräteinformationen:**
> ⚠️ Wohnzimmer Steckdose (shelly) hat um 14:32 die Verbindung verloren.
> 📍 Wohnzimmer  ·  Shelly Plus 1PM

**Zusammenfassung (Deutsch):**
> 📋 3 Gerät(e) seit der letzten Zusammenfassung betroffen:
> • Küchen-Sensor [Küche] (zha): offline seit 12.05. 07:15, wieder online um 07:42
> • Schlafzimmer Birne [Schlafzimmer] (hue): offline seit 12.05. 09:05 ⚠️ noch offline
> • Flur Bewegungsmelder (esphome): offline seit 12.05. 11:20, wieder online um 11:28

### Voraussetzungen

- Home Assistant 2023.6 oder neuer
- Mindestens eine unterstützte Integration eingerichtet

---

## Changelog

### v1.1.0 *(released)*

**Per-protocol alert delays**  
Each integration family can now have its own alert delay overriding the global setting. A built-in "Apply recommended delays" checkbox pre-fills all fields with sensible values for each protocol (2 min for ESPHome/Shelly/Tasmota, 5 min for Zigbee/Z-Wave, 20 min for passive BLE, 10 min for cloud integrations, and more).

**Watch label – custom offline indicators**  
Label any HA entity with a custom HA label name. Connection Observer monitors those entities and creates an offline event when their state turns `on`, and closes it when the state returns to `off`. This enables real-time monitoring of passive BLE devices (BTHome, GARDENA Bluetooth), cloud devices, or any custom scenario where `unavailable` is not used — pair it with a template binary sensor watching `last_updated` for a complete BTHome freshness monitor.

## Roadmap

### v1.2.0 — Label-based scope filtering *(planned)*

Use HA's label system to define monitoring scope without maintaining entity lists — monitor everything tagged `critical`, exclude anything tagged `ignore`.

---

## Contributing

Pull requests are welcome. Missing an integration? Open an issue or add the domain to `const.py` and submit a PR — it's a one-liner.

## License

[MIT](LICENSE)

---

## Appendix – Supported integrations

<details>
<summary>Show all 100+ supported integrations</summary>

| Category | Integration | Domain |
|---|---|---|
| **Zigbee / Z-Wave / Thread** | Zigbee (ZHA) | `zha` |
| | Zigbee (deCONZ) | `deconz` |
| | Z-Wave (Z-Wave JS) | `zwave_js` |
| | Matter | `matter` |
| | Thread (OTBR) | `otbr` |
| | RFXtrx (433 MHz) | `rfxtrx` |
| | MySensors | `mysensors` |
| | Insteon | `insteon` |
| | KNX | `knx` |
| | Velbus | `velbus` |
| **Bluetooth** | Bluetooth | `bluetooth` |
| | SwitchBot | `switchbot` |
| | GARDENA Bluetooth | `gardena_bluetooth` |
| **WiFi / LAN devices** | ESPHome | `esphome` |
| | Shelly | `shelly` |
| | Tasmota | `tasmota` |
| | Tuya | `tuya` |
| | WLED | `wled` |
| | TP-Link (Kasa/Tapo) | `tplink` |
| | TP-Link Omada | `tplink_omada` |
| | Broadlink | `broadlink` |
| **Lighting** | Philips Hue | `hue` |
| | IKEA TRÅDFRI | `tradfri` |
| | LIFX | `lifx` |
| | Nanoleaf | `nanoleaf` |
| | Yeelight | `yeelight` |
| | Xiaomi (Mi Home) | `xiaomi_miio` |
| **Speakers & media** | Sonos | `sonos` |
| | Google Cast (Chromecast) | `cast` |
| | Logitech Media Server | `squeezebox` |
| | Kodi | `kodi` |
| | Plex | `plex` |
| | Sony Bravia TV | `braviatv` |
| | Samsung TV | `samsungtv` |
| | LG webOS TV | `webostv` |
| | Android TV / Google TV | `androidtv` |
| | Apple TV | `apple_tv` |
| | Roku | `roku` |
| | Yamaha MusicCast | `yamaha_musiccast` |
| | Denon / Marantz AVR | `denon` |
| | Onkyo / Pioneer AVR | `onkyo` |
| | Logitech Harmony | `harmony` |
| **Climate & energy** | Netatmo | `netatmo` |
| | Tado | `tado` |
| | Daikin | `daikin` |
| | ecobee | `ecobee` |
| | Google Nest | `nest` |
| | HomeWizard Energy | `homewizard` |
| | Tibber | `tibber` |
| | SMA Solar | `sma` |
| | SolarEdge | `solaredge` |
| | Fronius | `fronius` |
| | Tesla Powerwall | `powerwall` |
| **Heating / HVAC** | Viessmann ViCare | `vicare` |
| | Vaillant (myVaillant) | `vaillant` |
| | Bosch Smart Home | `bosch_shc` |
| | Mitsubishi MelCloud | `melcloud` |
| | NIBE heat pump | `nibe_heatpump` |
| **Solar / energy (extended)** | Huawei Solar | `huawei_solar` |
| | Enphase Envoy | `enphase_envoy` |
| | GoodWe | `goodwe` |
| | Growatt | `growatt_server` |
| | EcoFlow | `ecoflow` |
| **Security & access** | Nuki Smart Lock | `nuki` |
| | August Smart Lock | `august` |
| | Yale Smart Alarm | `yale_smart_alarm` |
| | Ring | `ring` |
| | Blink | `blink` |
| | Arlo | `arlo` |
| | DoorBird | `doorbird` |
| | Reolink | `reolink` |
| | Amcrest | `amcrest` |
| | Eufy Security | `eufy_security` |
| | SimpliSafe | `simplisafe` |
| | Abode | `abode` |
| **Network & infrastructure** | UniFi (Ubiquiti) | `unifi` |
| | AVM FRITZ!Box | `fritz` |
| | MikroTik | `mikrotik` |
| | ASUS Router | `asusrouter` |
| | Synology NAS | `synology_dsm` |
| **Vacuum robots** | Roborock | `roborock` |
| | ECOVACS | `ecovacs` |
| | Neato Robotics | `neato` |
| **Household appliances** | LG ThinQ | `lg_thinq` |
| | Meross | `meross` |
| | Belkin WeMo | `wemo` |
| **Gates & garage doors** | myQ (Chamberlain / LiftMaster) | `myq` |
| | Nice G.O. | `nice_go` |
| **Local weather stations** | Ecowitt | `ecowitt` |
| | Ambient Weather Station | `ambient_station` |
| **Garden & household** | Husqvarna Automower | `husqvarna_automower` |
| | GARDENA Bluetooth | `gardena_bluetooth` |
| | iRobot Roomba | `roomba` |
| **Other / generic** | MQTT | `mqtt` |
| | HomeKit Controller | `homekit_controller` |
| | Lutron Caséta | `lutron_caseta` |

</details>
