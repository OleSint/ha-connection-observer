# Connection Observer

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/OleSint/ha-connection-observer)](https://github.com/OleSint/ha-connection-observer/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Deutsch weiter unten** ↓

---

## English

**Connection Observer** monitors your smart home devices and alerts you when they lose their connection — before you notice a stuck light switch or a missing sensor reading.

### Features

- **Protocol-based monitoring** – select entire integration families (Zigbee, Z-Wave, Hue, ESPHome, Shelly, Sonos, …) instead of configuring individual entities. 80+ integrations supported out of the box.
- **Immediate notifications** – get alerted the moment a device goes offline
- **Scheduled summaries** – receive a digest on configurable days and times listing everything that disconnected since the last summary, including whether the device came back online and when
- **Both modes simultaneously** – immediate + summary can both be active at once; summary is pre-selected by default
- **Reconnect notifications** – opt-in alert when a device comes back online
- **Per-entity exclusions** – exclude specific noisy entities from monitoring
- **Bilingual** – notification messages in English or German (configurable)
- **Persistent state** – events survive Home Assistant restarts; an HA restart itself never triggers a false disconnect alarm

### How it works

Connection Observer listens for entities transitioning to the `unavailable` state — this is the standard Home Assistant mechanism used by virtually all integrations when a device can no longer be reached. When a device with multiple entities goes offline, only **one** notification is sent per device (not one per entity).

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
4. **Step 2 – Notifications**: Select one or more notification services, configure immediate and/or summary notifications, and optionally exclude specific entities

All settings can be changed later via the **Configure** button on the integration card.

### Notification examples

**Immediate (English):**
> ⚠️ Living Room Plug (shelly) lost connection at 14:32.

**Summary (English):**
> 📋 3 device(s) affected since last summary:
> • Kitchen Sensor (zha): offline since 05/12 07:15, back online at 07:42
> • Bedroom Bulb (hue): offline since 05/12 09:05 ⚠️ still offline
> • Hallway Motion (esphome): offline since 05/12 11:20, back online at 11:28

### Requirements

- Home Assistant 2023.6 or newer
- At least one supported integration configured

---

## Deutsch

**Connection Observer** überwacht deine Smart-Home-Geräte und benachrichtigt dich, wenn die Verbindung abbricht — bevor du selbst merkst, dass ein Lichtschalter nicht mehr reagiert oder ein Sensor keine Werte mehr liefert.

### Funktionen

- **Protokollbasierte Überwachung** – ganze Integrationsfamilien auswählen (Zigbee, Z-Wave, Hue, ESPHome, Shelly, Sonos, …) statt einzelner Entitäten. Über 80 Integrationen werden unterstützt.
- **Sofortbenachrichtigung** – wird direkt gesendet, sobald ein Gerät offline geht
- **Geplante Zusammenfassung** – Sammelnachricht zu konfigurierbaren Tagen und Uhrzeiten mit allen Verbindungsabbrüchen seit der letzten Zusammenfassung (inkl. ob das Gerät zwischendurch wieder online war)
- **Beide Modi gleichzeitig** – Sofort + Zusammenfassung können parallel aktiv sein; Zusammenfassung ist standardmäßig vorausgewählt
- **Wiederverbindungsbenachrichtigung** – optionale Meldung, wenn ein Gerät wieder online geht
- **Entitäten ausschließen** – einzelne, störungsanfällige Entitäten von der Überwachung ausnehmen
- **Zweisprachig** – Benachrichtigungen auf Deutsch oder Englisch (konfigurierbar)
- **Persistenter Zustand** – Ereignisse überleben HA-Neustarts; ein HA-Neustart selbst löst keinen falschen Alarm aus

### Funktionsprinzip

Connection Observer überwacht, wann Entitäten den Status `unavailable` annehmen — das ist der Standard-Mechanismus in HA, den nahezu alle Integrationen verwenden, wenn ein Gerät nicht mehr erreichbar ist. Hat ein Gerät mehrere Entitäten, wird nur **eine** Benachrichtigung pro Gerät ausgelöst, nicht eine pro Entität.

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
4. **Schritt 2 – Benachrichtigungen**: Einen oder mehrere Benachrichtigungsdienste auswählen, Sofortalarm und/oder Zusammenfassung konfigurieren, optional Entitäten ausschließen

Alle Einstellungen können nachträglich über den **Konfigurieren**-Button der Integrationskarte geändert werden.

### Beispiel-Benachrichtigungen

**Sofort (Deutsch):**
> ⚠️ Wohnzimmer Steckdose (shelly) hat um 14:32 die Verbindung verloren.

**Zusammenfassung (Deutsch):**
> 📋 3 Gerät(e) seit der letzten Zusammenfassung betroffen:
> • Küchen-Sensor (zha): offline seit 12.05. 07:15, wieder online um 07:42
> • Schlafzimmer Birne (hue): offline seit 12.05. 09:05 ⚠️ noch offline
> • Flur Bewegungsmelder (esphome): offline seit 12.05. 11:20, wieder online um 11:28

### Voraussetzungen

- Home Assistant 2023.6 oder neuer
- Mindestens eine unterstützte Integration eingerichtet

---

## Contributing

Pull requests are welcome. Missing an integration? Open an issue or add the domain to `const.py` and submit a PR — it's a one-liner.

## License

[MIT](LICENSE)

---

## Appendix – Supported integrations

<details>
<summary>Show all 80+ supported integrations</summary>

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
| **Garden & household** | Husqvarna Automower | `husqvarna_automower` |
| | iRobot Roomba | `roomba` |
| **Other / generic** | MQTT | `mqtt` |
| | HomeKit Controller | `homekit_controller` |
| | Lutron Caséta | `lutron_caseta` |

</details>
