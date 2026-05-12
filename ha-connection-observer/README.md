# Connection Observer

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/OleSint/ha-connection-observer)](https://github.com/OleSint/ha-connection-observer/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Deutsch weiter unten** ↓

---

## English

**Connection Observer** monitors your smart home devices and alerts you when they lose their connection — before you notice a stuck light switch or a missing sensor reading.

### Features

- **Protocol-based monitoring** – select entire protocol stacks (Zigbee, Z-Wave, ESPHome, Thread, Bluetooth, …) instead of configuring individual entities
- **Immediate notifications** – get alerted the moment a device goes offline
- **Scheduled summaries** – receive a digest on configurable days and times listing everything that disconnected since the last summary, including whether the device came back online and when
- **Both modes simultaneously** – immediate + summary can both be active at once; summary is pre-selected by default
- **Reconnect notifications** – opt-in alert when a device comes back online
- **Per-entity exclusions** – exclude specific noisy entities from monitoring
- **Bilingual** – notification messages in English or German (configurable)
- **Persistent state** – events survive Home Assistant restarts; an HA restart itself never triggers a false disconnect alarm

### Supported protocols / integrations

| Protocol | Integration domain |
|---|---|
| Zigbee | `zha`, `deconz` |
| Z-Wave | `zwave_js` |
| Matter | `matter` |
| Thread | `otbr` |
| Bluetooth | `bluetooth` |
| ESPHome | `esphome` |
| Shelly | `shelly` |
| Tasmota | `tasmota` |
| Tuya | `tuya` |
| WLED | `wled` |
| MQTT | `mqtt` |
| HomeKit Controller | `homekit_controller` |
| Xiaomi (Mi Home) | `xiaomi_miio` |
| Lutron Caséta | `lutron_caseta` |
| Insteon | `insteon` |
| KNX | `knx` |

Only protocols that are actually configured in your HA instance will appear in the setup wizard.

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
3. **Step 1 – Protocols**: Select the connection protocols to monitor and choose your notification language
4. **Step 2 – Notifications**: Select your notification service and configure immediate and/or summary notifications

All settings can be changed later via the **Configure** button on the integration card.

### Notification examples

**Immediate (English):**
> ⚠️ Living Room Plug (zha) lost connection at 14:32.

**Summary (English):**
> 📋 3 device(s) affected since last summary:
> • Kitchen Sensor (zha): offline since 05/12 07:15, back online at 07:42
> • Bedroom Bulb (zha): offline since 05/12 09:05 ⚠️ still offline
> • Hallway Motion (esphome): offline since 05/12 11:20, back online at 11:28

### Requirements

- Home Assistant 2023.6 or newer
- At least one supported integration configured

---

## Deutsch

**Connection Observer** überwacht deine Smart-Home-Geräte und benachrichtigt dich, wenn die Verbindung abbricht — bevor du selbst merkst, dass ein Lichtschalter nicht mehr reagiert oder ein Sensor keine Werte mehr liefert.

### Funktionen

- **Protokollbasierte Überwachung** – ganze Protokollstapel auswählen (Zigbee, Z-Wave, ESPHome, Thread, Bluetooth, …) statt einzelner Entitäten
- **Sofortbenachrichtigung** – wird direkt gesendet, sobald ein Gerät offline geht
- **Geplante Zusammenfassung** – Sammelnachricht zu konfigurierbaren Tagen und Uhrzeiten mit allen Verbindungsabbrüchen seit der letzten Zusammenfassung (inkl. ob das Gerät zwischendurch wieder online war)
- **Beide Modi gleichzeitig** – Sofort + Zusammenfassung können parallel aktiv sein; Zusammenfassung ist standardmäßig vorausgewählt
- **Wiederverbindungsbenachrichtigung** – optionale Meldung, wenn ein Gerät wieder online geht
- **Entitäten ausschließen** – einzelne, störungsanfällige Entitäten von der Überwachung ausnehmen
- **Zweisprachig** – Benachrichtigungen auf Deutsch oder Englisch (konfigurierbar)
- **Persistenter Zustand** – Ereignisse überleben HA-Neustarts; ein HA-Neustart selbst löst keinen falschen Alarm aus

### Unterstützte Protokolle

Alle oben genannten Protokolle werden unterstützt. Im Einrichtungsassistenten erscheinen nur Protokolle, die in deiner HA-Instanz tatsächlich konfiguriert sind.

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
3. **Schritt 1 – Protokolle**: Zu überwachende Protokolle und Benachrichtigungssprache auswählen
4. **Schritt 2 – Benachrichtigungen**: Benachrichtigungsdienst, Sofortalarm und/oder Zusammenfassung konfigurieren

Alle Einstellungen können nachträglich über den **Konfigurieren**-Button der Integrationskarte geändert werden.

### Beispiel-Benachrichtigungen

**Sofort (Deutsch):**
> ⚠️ Wohnzimmer Steckdose (zha) hat um 14:32 die Verbindung verloren.

**Zusammenfassung (Deutsch):**
> 📋 3 Gerät(e) seit der letzten Zusammenfassung betroffen:
> • Küchen-Sensor (zha): offline seit 12.05. 07:15, wieder online um 07:42
> • Schlafzimmer Birne (zha): offline seit 12.05. 09:05 ⚠️ noch offline
> • Flur Bewegungsmelder (esphome): offline seit 12.05. 11:20, wieder online um 11:28

### Voraussetzungen

- Home Assistant 2023.6 oder neuer
- Mindestens eine unterstützte Integration eingerichtet

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

## License

[MIT](LICENSE)
