# Connection Observer – Dokumentation (Deutsch)

**Version:** 1.2.0  
**Repository:** [github.com/OleSint/ha-connection-observer](https://github.com/OleSint/ha-connection-observer)

---

## Inhaltsverzeichnis

1. [Was ist Connection Observer?](#1-was-ist-connection-observer)
2. [Funktionsprinzip](#2-funktionsprinzip)
3. [Installation](#3-installation)
4. [Setup-Assistent](#4-setup-assistent)
5. [Konfigurationsoptionen](#5-konfigurationsoptionen)
   - [Protokollspezifische Verzögerungen](#protokollspezifische-verzögerungen)
   - [Watch-Label – eigene Offline-Indikatoren](#watch-label--eigene-offline-indikatoren)
6. [Benachrichtigungsvorlagen](#6-benachrichtigungsvorlagen)
7. [HA-Reparaturen-Integration](#7-ha-reparaturen-integration)
8. [Entitäten](#8-entitäten)
9. [Services](#9-services)
10. [Benachrichtigungsformate](#10-benachrichtigungsformate)
11. [Fortgeschrittene Anwendungsfälle](#11-fortgeschrittene-anwendungsfälle)
12. [Fehlerbehebung](#12-fehlerbehebung)
13. [Bekannte Einschränkungen](#13-bekannte-einschränkungen)

---

## 1. Was ist Connection Observer?

Connection Observer ist eine benutzerdefinierte Home Assistant Integration, die kontinuierlich die Verbindungen deiner Smart-Home-Geräte überwacht und dich informiert, wenn etwas offline geht — bevor du selbst merkst, dass ein Lichtschalter nicht mehr reagiert oder ein Sensor keine Werte mehr liefert.

**Die Kernidee** ist die Überwachung nach *Protokollfamilie* statt nach einzelnen Entitäten. Statt 200 Entitäten einzeln auszuwählen, wählst du einfach „alle Zigbee-Geräte überwachen" oder „alle ESPHome-Geräte überwachen". Jedes Gerät dieser Integrationsfamilie wird automatisch abgedeckt — einschließlich neuer Geräte, die du später hinzufügst.

---

## 2. Funktionsprinzip

### Der `unavailable`-Status

Home Assistant verfügt über einen eingebauten Mechanismus, um anzuzeigen, dass ein Gerät nicht mehr erreichbar ist: Es setzt alle Entitäten des Geräts auf den Status `unavailable`. Dies geschieht automatisch, wenn:

- Ein Zigbee- oder Z-Wave-Gerät nicht mehr auf den Koordinator antwortet
- Ein WLAN-Gerät (ESPHome, Shelly usw.) im Netzwerk nicht mehr erreichbar ist
- Eine Hue-Lampe an der Wand ausgeschaltet wird und die Bridge den Kontakt verliert
- Eine andere Integration erkennt, dass die Kommunikation unterbrochen wurde

Connection Observer überwacht genau diesen Übergang: von einem beliebigen Status → `unavailable`. Wird dieser erkannt, wird ein *Verbindungsabbruch-Ereignis* für das betroffene Gerät erstellt.

### Deduplizierung auf Geräteebene

Die meisten Geräte haben mehrere Entitäten in Home Assistant. Ein Zigbee-Stecker könnte Entitäten für den Schaltstatus, die aktuelle Leistung, die Gesamtenergie, die Spannung und mehr haben. Wenn dieser Stecker offline geht, werden alle Entitäten gleichzeitig `unavailable`.

Connection Observer ermittelt über die HA-Geräteregistrierung, zu welchem *Gerät* eine Entität gehört, und erstellt nur **ein Ereignis pro Gerät** — unabhängig davon, wie viele Entitäten es hat. Das bedeutet eine Benachrichtigung pro Gerät, nicht fünf.

### Startschutz

Wenn Home Assistant neu startet, brauchen alle Integrationen einen Moment, um ihre Geräte wieder zu verbinden. In diesem Zeitfenster durchlaufen viele Entitäten kurzzeitig den Status `unavailable`. Connection Observer wartet 60 Sekunden, nachdem HA vollständig gestartet ist, bevor es mit dem Tracking beginnt. Das verhindert eine Flut von Fehlalarmen bei jedem HA-Neustart.

### Persistenter Speicher

Alle Verbindungsabbruch-Ereignisse werden im integrierten HA-Speicher abgelegt (`~/.homeassistant/.storage/`). Ereignisse überleben HA-Neustarts und werden bis zu 30 Tage aufbewahrt.

### Watchdog

Alle 5 Minuten prüft Connection Observer aktiv, ob Geräte mit offenen Ereignissen tatsächlich noch nicht erreichbar sind. Hat ein Gerät sich wieder verbunden, ohne ein `state_changed`-Event auszulösen, erkennt der Watchdog dies und schließt das Ereignis ab.

---

## 3. Installation

### Über HACS (empfohlen)

1. Stelle sicher, dass HACS in deiner HA-Instanz installiert ist. Falls nicht, folge der [HACS-Installationsanleitung](https://hacs.xyz/docs/setup/download).
2. Öffne **HACS → Integrationen** in der HA-Seitenleiste.
3. Klicke auf das **Drei-Punkte-Menü** (oben rechts) → **Benutzerdefinierte Repositories**.
4. Gib `https://github.com/OleSint/ha-connection-observer` als URL ein und wähle **Integration** als Kategorie. Klicke auf **Hinzufügen**.
5. Suche nach **Connection Observer** in der HACS-Integrationsliste und klicke auf **Herunterladen**.
6. **Home Assistant neu starten.**
7. Gehe nach dem Neustart zu **Einstellungen → Geräte & Dienste → Integration hinzufügen** und suche nach **Connection Observer**.

### Manuelle Installation

1. Lade die neueste Version von der [GitHub-Releases-Seite](https://github.com/OleSint/ha-connection-observer/releases) herunter.
2. Extrahiere das Archiv und kopiere den Ordner `custom_components/connection_observer` in dein HA-Konfigurationsverzeichnis unter `config/custom_components/connection_observer`.
3. **Home Assistant neu starten.**
4. Gehe nach dem Neustart zu **Einstellungen → Geräte & Dienste → Integration hinzufügen** und suche nach **Connection Observer**.

---

## 4. Setup-Assistent

Der Setup-Assistent führt dich durch fünf Schritte. Alle Einstellungen können anschließend über den **Konfigurieren**-Button der Integrationskarte geändert werden.

### Schritt 1 – Protokolle

**Was du hier auswählst, legt fest, welche Geräte überwacht werden.**

Der Assistent zeigt nur Integrationsfamilien an, die in deiner HA-Instanz tatsächlich eingerichtet sind.

| Feld | Beschreibung |
|---|---|
| **Zu überwachende Protokolle** | Mehrfachauswahl. Wähle eine oder mehrere Integrationsfamilien aus. |
| **Benachrichtigungssprache** | Wähle Englisch, Deutsch, Français, Nederlands oder Español. |

> **Tipp:** Du kannst Protokolle jederzeit hinzufügen oder entfernen. Neu hinzugefügte Geräte eines ausgewählten Protokolls werden automatisch erfasst.

> **Zigbee2MQTT-Nutzer:** Zigbee2MQTT-Geräte erscheinen in HA unter dem `mqtt`-Integrations-Domain — es gibt keinen separaten Zigbee2MQTT-Eintrag. Wähle **MQTT**, um sie zu überwachen. Beachte dabei, dass dadurch auch alle anderen MQTT-basierten Geräte erfasst werden (z.B. Tasmota, eigene Sensoren). Für eine feinere Steuerung ist eine Label-basierte Filterung in einer zukünftigen Version geplant.
>
> ⚠️ **Wichtig:** Connection Observer erkennt Geräte nur, wenn HA sie auf `unavailable` setzt. Zigbee2MQTT tut dies standardmäßig **nicht** — die Verfügbarkeitsprüfung muss erst aktiviert werden: **Zigbee2MQTT → Einstellungen → Verfügbarkeit → aktiviert**. Ohne diese Einstellung bleibt Connection Observer für Z2M-Geräte wirkungslos.

### Schritt 2 – Benachrichtigungen

**Lege fest, wie und wann du Benachrichtigungen erhältst.**

| Feld | Beschreibung |
|---|---|
| **Benachrichtigungsdienst(e)** | Mehrfachauswahl. Wähle einen oder mehrere `notify.*`-Dienste. |
| **Sofortbenachrichtigung bei Verbindungsabbruch** | Wenn aktiviert, wird direkt eine Benachrichtigung gesendet. Standard: **aus**. |
| **Geplante Zusammenfassung** | Wenn aktiviert, wird eine Zusammenfassung zur konfigurierten Zeit gesendet. Standard: **ein**. |
| **Uhrzeit der Zusammenfassung** | Uhrzeit für die Zusammenfassungsbenachrichtigung. |
| **Tage der Zusammenfassung** | Wochentage für die Zusammenfassung. Standard: täglich. |
| **Benachrichtigung bei Wiederverbindung** | Opt-in. Benachrichtigung, wenn ein Gerät wieder online geht. Standard: **aus**. |

### Schritt 3 – Test

Ein optionaler Testschritt sendet eine Benachrichtigung an alle ausgewählten Dienste, damit du prüfen kannst, ob alles korrekt funktioniert.

- Aktiviere **Testbenachrichtigung jetzt senden** (vorausgewählt) und klicke auf Weiter.
- Deaktiviere das Kontrollkästchen, um diesen Schritt zu überspringen.
- Schlägt der Test fehl, wird eine Fehlermeldung angezeigt. Du kannst es erneut versuchen oder das Kontrollkästchen deaktivieren und trotzdem fortfahren.

### Schritt 4 – Erweitert

**Alle Felder in diesem Schritt sind optional. Der Wert 0 deaktiviert die jeweilige Funktion.**  
Die hier eingestellte **globale Verzögerung** gilt für alle Protokolle, sofern in Schritt 5 kein eigener Wert gesetzt wird.

| Feld | Beschreibung |
|---|---|
| **Verzögerung** | Minuten offline, bevor ein Ereignis erstellt wird. Standard: **0** (sofort). |
| **Cooldown** | Mindestabstand zwischen Sofortbenachrichtigungen pro Gerät. Standard: **0** (kein Limit). |
| **Mindestausfallzeit für Zusammenfassung** | Ereignisse kürzer als dieser Wert erscheinen nicht in der Zusammenfassung. Standard: **0** (alle Ereignisse). |
| **Raum / Bereich anzeigen** | HA-Bereichsname in Benachrichtigungen einblenden. Standard: **aus**. |
| **Hersteller & Modell anzeigen** | Geräteinformationen in Sofortmeldungen einblenden. Standard: **aus**. |
| **Ausgeschlossene Entitätsdomänen** | Ganze Entitätsdomänen von der Überwachung ausschließen (z. B. `sensor`, `button`). Aus der Liste auswählen oder eigene Domäne eingeben. `device_tracker`-Entitäten werden immer automatisch ignoriert und müssen hier nicht eingetragen werden. |
| **Ausgeschlossene Geräte** | Liste von Geräten, die vollständig von der Überwachung ausgenommen werden. Es werden nur Geräte angezeigt, die mindestens eine Entität mit einem konfigurierten Protokoll besitzen — virtuelle Dienste (HACS, Supervisor, Add-ons usw.) erscheinen nicht. Wird ein Gerät ausgeschlossen, während es gerade offline ist, wird es sofort aus der Offline-Liste entfernt und ein offener HA-Reparatureintrag automatisch aufgelöst. |

### Schritt 5 – Experte

**Beide Felder sind optional. Überspringe diesen Schritt, wenn du nur die globale Verzögerung benötigst.**

#### Protokollspezifische Verzögerungen

Jedes in Schritt 1 gewählte Protokoll erscheint hier mit einem eigenen Verzögerungsfeld. Der Wert **0** bedeutet „globale Verzögerung aus Schritt 4 verwenden". Ein positiver Wert überschreibt die globale Verzögerung für dieses Protokoll.

**Tipp: Ein-Klick-Empfehlungen**  
Setze das Häkchen bei **Empfohlene Verzögerungen für alle Protokolle anwenden** und klicke auf Weiter. Alle Felder werden automatisch mit den empfohlenen Werten gefüllt. Du kannst einzelne Werte danach noch anpassen.

Die Empfehlungen basieren auf den typischen Verbindungseigenschaften der jeweiligen Protokollfamilie:
- Direkte TCP-Protokolle (ESPHome, Shelly, Tasmota) → **2 min** (persistente Verbindung, schnelle Erkennung)
- Lokale Mesh-Protokolle (ZHA, Z-Wave JS) → **5 min** (Mesh-Routing braucht einen Moment)
- Passives BLE (BTHome, GARDENA Bluetooth) → **20 min** (seltene Advertisement-Zyklen)
- Cloud-Protokolle (Tuya, Nest, Ring, Tibber …) → **10 min** (Polling-Latenz)

Die vollständige Referenztabelle findest du in [Abschnitt 5](#protokollspezifische-verzögerungen).

#### Watch-Label – eigene Offline-Indikatoren

Gib hier den Namen eines HA-Labels ein (z. B. `offline_anzeige`). Jede Entität, der du dieses Label in der HA-Label-Verwaltung zuweist, wird von Connection Observer als eigener Offline-Indikator behandelt:

- Zustand der Entität wechselt auf **`on`** → Connection Observer erstellt ein Offline-Ereignis (Protokoll wird als `custom` angezeigt)
- Zustand der Entität wechselt auf **`off`** → Connection Observer markiert das Gerät als wieder online

Das Feature ist bewusst generisch: Du kannst jede beliebige Entität labeln — einen Template-Binärsensor, einen Helper oder eine andere binäre Entität.

**Typischer Anwendungsfall:** Passive BLE-Geräte (BTHome-Sensoren, GARDENA Bluetooth) können nicht in Echtzeit über den `unavailable`-Status überwacht werden. Siehe [Bekannte Einschränkungen](#13-bekannte-einschränkungen) und [Watch-Label](#watch-label--eigene-offline-indikatoren) in Abschnitt 5 für ein vollständiges Schritt-für-Schritt-Beispiel.

---

## 5. Konfigurationsoptionen

Alle Einstellungen aus dem Setup-Assistenten können jederzeit über **Einstellungen → Geräte & Dienste → Connection Observer → Konfigurieren** geändert werden.

Zusätzlich zu den Wizard-Einstellungen bietet die Optionsseite:

### Testbenachrichtigung

Nach dem Speichern der Einstellungen folgt ein kurzer Testschritt. Aktiviere **Testbenachrichtigung jetzt senden** und klicke auf Weiter, um einen Live-Test an alle konfigurierten Dienste zu senden. Deaktiviere das Kontrollkästchen, um den Schritt zu überspringen. Besonders nützlich, wenn du den Benachrichtigungsdienst gewechselt hast.

### Domänenausschlüsse

Ganze Entitätsdomänen können auf der Optionsseite ausgeschlossen werden (identisch mit dem Feld im Erweitert-Schritt des Wizards). `device_tracker` wird unabhängig von dieser Einstellung immer automatisch ignoriert.

### HA-Reparaturen-Schwellwert

Legt fest, nach wie vielen Stunden ein dauerhafter Eintrag unter **Einstellungen → Reparaturen** erstellt wird. Der Wert `0` deaktiviert diese Funktion. Standard: **24 Stunden**.

Siehe [Abschnitt 7](#7-ha-reparaturen-integration) für Details.

### Benachrichtigungsvorlagen

Sieben optionale Textfelder ermöglichen es, das Standard-Benachrichtigungsformat für jeden Benachrichtigungstyp anzupassen. Ein leeres Feld verwendet den sprachabhängigen Standard.

Siehe [Abschnitt 6](#6-benachrichtigungsvorlagen) für Details.

### Protokollspezifische Verzögerungen

Jedes gewählte Protokoll kann eine eigene Verzögerung erhalten, die den globalen Wert überschreibt. Der Wert **0** (oder kein Eintrag) bedeutet Fallback auf die globale Verzögerung.

**Ein-Klick-Setup:** Im Experte-Schritt (Wizard) bzw. auf der Experte-Seite (Optionen) das Häkchen bei **Empfohlene Verzögerungen anwenden** setzen und auf Weiter klicken.

| Protokoll | Domain | Empf. Verzögerung | Begründung |
|---|---|---:|---|
| Zigbee (ZHA) | `zha` | 5 min | Mesh-Routing braucht einen Moment |
| Zigbee (deCONZ) | `deconz` | 5 min | Mesh-Routing braucht einen Moment |
| Z-Wave (Z-Wave JS) | `zwave_js` | 5 min | Mesh-Routing braucht einen Moment |
| Matter | `matter` | 5 min | Mesh-ähnliches Verhalten |
| Thread (OTBR) | `otbr` | 5 min | Thread-Mesh |
| Bluetooth | `bluetooth` | 10 min | BLE-Verbindungsaufbau ist langsamer |
| BTHome | `bthome` | 20 min | Passives BLE – seltene Advertisements |
| RFXtrx (433 MHz) | `rfxtrx` | 10 min | Einweg-RF, kein ACK |
| MySensors | `mysensors` | 10 min | Langsames Polling |
| Insteon | `insteon` | 5 min | Proprietärer Bus, polling-basiert |
| KNX | `knx` | 5 min | Drahtbus, zuverlässig aber polling-basiert |
| Velbus | `velbus` | 5 min | Drahtbus |
| ESPHome | `esphome` | 2 min | Persistentes TCP, sehr schnelle Erkennung |
| Shelly | `shelly` | 2 min | Persistentes TCP, sehr schnelle Erkennung |
| Tasmota | `tasmota` | 2 min | Persistentes TCP, sehr schnelle Erkennung |
| Tuya | `tuya` | 5 min | Cloud-Polling |
| WLED | `wled` | 2 min | Lokales TCP |
| TP-Link (Kasa/Tapo) | `tplink` | 3 min | Lokales TCP |
| TP-Link Omada | `tplink_omada` | 3 min | Lokales TCP |
| Broadlink | `broadlink` | 3 min | Lokales TCP |
| Philips Hue | `hue` | 3 min | Lokale Hue-Bridge |
| IKEA TRÅDFRI | `tradfri` | 5 min | IKEA-Hub kann langsam reagieren |
| LIFX | `lifx` | 3 min | Lokales UDP/TCP |
| Nanoleaf | `nanoleaf` | 3 min | Lokales TCP |
| Yeelight | `yeelight` | 2 min | Lokales TCP |
| Xiaomi Mi Home | `xiaomi_miio` | 5 min | Lokal + Cloud-Mix |
| Sonos | `sonos` | 3 min | Lokales Netzwerk |
| Google Cast | `cast` | 3 min | Lokales Netzwerk |
| Logitech Media Server | `squeezebox` | 5 min | Server-abhängig |
| Kodi | `kodi` | 3 min | Lokales Netzwerk |
| Plex | `plex` | 5 min | Server-abhängig |
| Sony Bravia TV | `braviatv` | 3 min | Lokales Netzwerk |
| Samsung TV | `samsungtv` | 3 min | Lokales Netzwerk |
| LG webOS TV | `webostv` | 3 min | Lokales Netzwerk |
| Android TV / Google TV | `androidtv` | 3 min | Lokales Netzwerk |
| Apple TV | `apple_tv` | 3 min | Lokales Netzwerk |
| Roku | `roku` | 3 min | Lokales Netzwerk |
| Yamaha MusicCast | `yamaha_musiccast` | 3 min | Lokales Netzwerk |
| Denon / Marantz AVR | `denon` | 3 min | Lokales Netzwerk |
| Onkyo / Pioneer AVR | `onkyo` | 3 min | Lokales Netzwerk |
| Logitech Harmony | `harmony` | 5 min | Hub-basiert |
| Netatmo | `netatmo` | 10 min | Cloud-Polling, höhere Latenz |
| Tado | `tado` | 10 min | Cloud-Polling |
| Daikin | `daikin` | 5 min | Lokal + Cloud-Mix |
| ecobee | `ecobee` | 10 min | Cloud-Polling |
| Google Nest | `nest` | 10 min | Cloud-Polling |
| HomeWizard Energy | `homewizard` | 3 min | Lokales LAN |
| Tibber | `tibber` | 10 min | Cloud-API |
| SMA Solar | `sma` | 10 min | Cloud / lokales Modbus |
| SolarEdge | `solaredge` | 10 min | Cloud-Polling |
| Fronius | `fronius` | 10 min | Cloud-Polling |
| Tesla Powerwall | `powerwall` | 5 min | Meist lokal |
| Nuki Smart Lock | `nuki` | 5 min | BLE-Bridge / Cloud |
| August Smart Lock | `august` | 5 min | Cloud |
| Yale Smart Alarm | `yale_smart_alarm` | 5 min | Cloud |
| Ring | `ring` | 10 min | Cloud-Kamera |
| Blink | `blink` | 10 min | Cloud-Kamera |
| Arlo | `arlo` | 10 min | Cloud-Kamera |
| DoorBird | `doorbird` | 3 min | Lokales LAN |
| Reolink | `reolink` | 3 min | Lokales LAN |
| Amcrest | `amcrest` | 3 min | Lokales LAN |
| Eufy Security | `eufy_security` | 5 min | Cloud |
| SimpliSafe | `simplisafe` | 10 min | Cloud |
| Abode | `abode` | 10 min | Cloud |
| UniFi (Ubiquiti) | `unifi` | 3 min | Lokales LAN |
| AVM FRITZ!Box | `fritz` | 5 min | Lokales LAN |
| MikroTik | `mikrotik` | 3 min | Lokales LAN |
| ASUS Router | `asusrouter` | 3 min | Lokales LAN |
| Synology NAS | `synology_dsm` | 3 min | Lokales LAN |
| Viessmann ViCare | `vicare` | 10 min | Cloud |
| Vaillant (myVaillant) | `vaillant` | 10 min | Cloud |
| Bosch Smart Home | `bosch_shc` | 5 min | Lokaler Controller |
| Mitsubishi MelCloud | `melcloud` | 10 min | Cloud |
| NIBE Wärmepumpe | `nibe_heatpump` | 10 min | Cloud / lokal |
| Huawei Solar | `huawei_solar` | 5 min | Lokales Modbus |
| Enphase Envoy | `enphase_envoy` | 5 min | Lokales LAN |
| GoodWe | `goodwe` | 10 min | Cloud |
| Growatt | `growatt_server` | 10 min | Cloud |
| EcoFlow | `ecoflow` | 10 min | Cloud |
| Roborock | `roborock` | 3 min | Lokal + Cloud |
| ECOVACS | `ecovacs` | 5 min | Cloud |
| Neato Robotics | `neato` | 5 min | Cloud |
| LG ThinQ | `lg_thinq` | 5 min | Cloud |
| Meross | `meross` | 3 min | Lokal + Cloud |
| Belkin WeMo | `wemo` | 3 min | Lokales LAN |
| myQ (Chamberlain / LiftMaster) | `myq` | 5 min | Cloud |
| Nice G.O. | `nice_go` | 5 min | Cloud |
| Ecowitt | `ecowitt` | 10 min | Lokal, aber selten kritisch |
| Ambient Weather Station | `ambient_station` | 10 min | Cloud / lokal |
| Husqvarna Automower | `husqvarna_automower` | 10 min | Cloud |
| GARDENA Bluetooth | `gardena_bluetooth` | 20 min | Passives BLE |
| MQTT | `mqtt` | 5 min | Je nach Gerät anpassen – sehr unterschiedlich |
| HomeKit Controller | `homekit_controller` | 5 min | Lokales HomeKit |
| Lutron Caséta | `lutron_caseta` | 3 min | Lokale Bridge |
| SwitchBot | `switchbot` | 10 min | BLE / Cloud |
| iRobot Roomba | `roomba` | 5 min | Cloud |

> ⚠️ **Für Entwickler:** Wird ein neues Protokoll in `KNOWN_PROTOCOLS` (`const.py`) hinzugefügt, muss zwingend ein passender Eintrag in `PROTOCOL_DELAY_HINTS` ergänzt werden — und eine neue Zeile in dieser Tabelle in allen fünf Sprachdokumentationen.

---

### Watch-Label – eigene Offline-Indikatoren

Das **Watch-Label**-Feature ermöglicht die Überwachung von *beliebigen* Geräten, die Connection Observer nicht über den normalen `unavailable`-Pfad überwachen kann — zum Beispiel:

- **Passive BLE-Sensoren** (BTHome, GARDENA Bluetooth): keine persistente Verbindung, HA setzt `unavailable` erst nach Stunden
- **Cloud-Geräte**, die im HA-Status "available" bleiben, obwohl das physische Gerät defekt oder nicht erreichbar ist
- **Jedes eigene Szenario**, bei dem du einen Binärsensor bauen kannst, der den echten Verbindungsstatus abbildet

#### Funktionsprinzip

1. Erstelle einen **Template-Binärsensor** (oder eine andere binäre Entität), der `on` ist wenn das Gerät offline ist, und `off` wenn es online ist.
2. Lege in der HA-Label-Verwaltung (**Einstellungen → Labels**) ein Label mit dem exakten Namen an, den du im Experte-Schritt konfiguriert hast (z. B. `offline_anzeige`).
3. Weise dem Template-Binärsensor dieses Label zu.
4. Connection Observer erkennt automatisch alle Entitäten mit diesem Label und überwacht ihren Zustand:
   - `on` → erstellt ein Offline-Ereignis (Protokoll wird als `custom` angezeigt)
   - `off` → markiert das Gerät als wieder online

#### Beispiel: BTHome-Türsensor – Frischheitsprüfung

Erstelle einen Template-Binärsensor, der prüft, ob das letzte Update mehr als 2 Stunden zurückliegt:

```yaml
# configuration.yaml
template:
  - binary_sensor:
      - name: "BTHome Tür Offline-Anzeige"
        unique_id: bthome_tuer_offline_anzeige
        state: >
          {{ (now() - states.sensor.bthome_tuer_kontakt.last_updated).total_seconds() > 7200 }}
        device_class: problem
```

Dann:
1. Unter **Einstellungen → Labels** ein Label `offline_anzeige` anlegen
2. Unter **Einstellungen → Geräte & Dienste → Entitäten** → `binary_sensor.bthome_tuer_offline_anzeige` suchen → Label `offline_anzeige` zuweisen
3. Im Experte-Schritt von Connection Observer bei **Watch-Label** `offline_anzeige` eintragen

Connection Observer erstellt jetzt ein Offline-Ereignis, sobald der BTHome-Sensor seit über 2 Stunden keinen Wert gemeldet hat — und schließt es automatisch, wenn ein neuer Wert eintrifft.

> **Tipp:** Du kannst mehrere Entitäten mit demselben Watch-Label versehen. Jede wird unabhängig überwacht. Der in Benachrichtigungen angezeigte Gerätename ist der Anzeigename der gelabelten Entität.

---

### Empfohlene Startkonfiguration

- **Sofortbenachrichtigung:** aus
- **Zusammenfassung:** ein, täglich um 08:00 Uhr
- **Globale Verzögerung:** 5 Minuten (vermeidet Fehlalarme durch kurze WLAN-Aussetzer)
- **Protokollspezifische Verzögerungen:** „Empfehlungen anwenden" für einen schnellen Start nutzen
- **Mindestausfallzeit:** 5 Minuten (hält die Zusammenfassung übersichtlich)
- **Bereich anzeigen:** ein (macht Benachrichtigungen deutlich lesbarer)
- **HA-Reparaturen-Schwellwert:** 24 Stunden
- **Watch-Label:** für passive BLE- oder eigene Geräte einrichten, wenn gewünscht

---

## 6. Benachrichtigungsvorlagen

Connection Observer sendet drei Arten von Benachrichtigungen: Sofort (Verbindungsabbruch), Wiederverbindung und Zusammenfassung. Jeder Typ hat einen Titel und einen Nachrichtentext, die unabhängig voneinander angepasst werden können.

### Verfügbare Vorlagen

Alle Vorlagenfelder befinden sich unter **Einstellungen → Geräte & Dienste → Connection Observer → Konfigurieren** am Ende der Optionsseite.

| Vorlagenschlüssel | Gilt für | Verfügbare Variablen |
|---|---|---|
| `tmpl_imm_title` | Sofortbenachrichtigung – Titel | `{device_name}` `{protocol}` `{time}` `{area}` `{model}` |
| `tmpl_imm_msg` | Sofortbenachrichtigung – Nachrichtentext | `{device_name}` `{protocol}` `{time}` `{area}` `{model}` |
| `tmpl_rec_title` | Wiederverbindung – Titel | `{device_name}` |
| `tmpl_rec_msg` | Wiederverbindung – Nachrichtentext | `{device_name}` |
| `tmpl_sum_title` | Zusammenfassung – Titel | `{count}` |
| `tmpl_sum_resolved` | Zusammenfassung – Zeile für abgeschlossenes Ereignis | `{device_name}` `{area}` `{protocol}` `{time_offline}` `{time_online}` |
| `tmpl_sum_ongoing` | Zusammenfassung – Zeile für noch offline | `{device_name}` `{area}` `{protocol}` `{time_offline}` |

### Hinweise zu den Variablen

- `{area}` ist vorformatiert als ` [Raumname]` (mit vorangehendem Leerzeichen), wenn die Option *Raum/Bereich anzeigen* aktiv ist, oder als leerer String.
- `{model}` ist `Hersteller – Modell` oder leer.
- `{time}` / `{time_offline}` / `{time_online}` sind als `HH:MM` formatiert. Bei `{time_offline}` in der Zusammenfassung wird das Datum vorangestellt (`TT.MM. HH:MM` auf Deutsch).

### Wichtige Hinweise

- Bei einer benutzerdefinierten `tmpl_imm_msg` wird die automatische zweite Zeile mit Bereich und Modell (📍 …) **nicht** angehängt. Füge `{area}` und `{model}` in deine Vorlage ein, wenn du diese Informationen möchtest.
- Vorlagenfehler (z.B. ein Tippfehler im Variablennamen) werden als Warnungen protokolliert.

---

## 7. HA-Reparaturen-Integration

Wenn ein Gerät länger als den konfigurierten Schwellwert (Standard: 24 Stunden) offline ist, erstellt Connection Observer einen persistenten Eintrag unter **Einstellungen → Reparaturen**. Dies ergänzt die regulären Benachrichtigungen.

### Was der Reparatureintrag zeigt

Der Eintrag enthält:
- Den Gerätenamen
- Das Protokoll / die Integration
- Den Zeitstempel, seit wann das Gerät offline ist

### Automatische Auflösung

Sobald das Gerät wieder online geht — entweder durch ein `state_changed`-Event oder über den Watchdog — wird der Reparatureintrag **automatisch gelöscht**.

### Deaktivieren

Setze **HA-Reparaturen-Eintrag nach N Stunden offline** auf `0` in den Optionen.

---

## 8. Entitäten

Connection Observer erstellt drei Entitäten pro Integrationsinstanz.

### `sensor.connection_observer_offline_devices`

**Typ:** Sensor | **Einheit:** devices | **Icon:** `mdi:lan-disconnect`

Zeigt die Anzahl der aktuell offline befindlichen Geräte.

**Zustandsattribute:**

| Attribut | Beschreibung |
|---|---|
| `devices` | Flache Liste der Gerätenamen, die aktuell offline sind. |
| `by_protocol` | Aufschlüsselung nach Protokoll: Anzahl offline und detaillierte Geräteliste je Integrationsfamilie. |

Das Attribut `by_protocol` hat folgende Struktur:

```yaml
by_protocol:
  shelly:
    offline: 1
    devices:
      - name: "Steckdose Küche"
        offline_since: "22.05. 14:30"
        offline_duration: "2h 15m"
  bthome:
    offline: 0
    devices: []
```

Nur Protokolle mit mindestens einem aktuell offline Gerät erscheinen in diesem Attribut.

**Beispiel — Markdown-Karte mit Protokoll-Statusübersicht:**
```yaml
type: markdown
content: >
  {% set proto = state_attr('sensor.connection_observer_offline_devices', 'by_protocol') %}
  {% for p, data in proto.items() %}
  **{{ p }}**: {{ data.devices | map(attribute='name') | join(', ') }}
  (offline seit {{ data.devices[0].offline_since }})
  {% endfor %}
```

**Beispiel in einer Automatisierung:**
```yaml
condition:
  - condition: numeric_state
    entity_id: sensor.connection_observer_offline_devices
    above: 0
```

---

### `sensor.connection_observer_pending_summary_events`

**Typ:** Sensor | **Einheit:** events | **Icon:** `mdi:clock-alert-outline`

Zeigt die Anzahl der Ereignisse, die noch nicht in einer Zusammenfassung enthalten waren. Wird nach dem Senden einer Zusammenfassung oder nach `clear_history` auf 0 zurückgesetzt.

---

### `binary_sensor.connection_observer_connection_problem`

**Typ:** Binärsensor | **Geräteklasse:** `problem` | **Icon:** `mdi:check-network`

- **`EIN`** – mindestens ein Gerät ist aktuell offline
- **`AUS`** – alle überwachten Geräte sind erreichbar

**Beispiel – Alarm, wenn Problem länger als 10 Minuten besteht:**
```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.connection_observer_connection_problem
    to: "on"
    for:
      minutes: 10
action:
  - service: notify.mobile_app_phone
    data:
      message: "Ein Gerät ist seit über 10 Minuten offline!"
```

---

## 9. Services

### `connection_observer.send_summary_now`

Sendet sofort eine Zusammenfassung aller ausstehenden Ereignisse. Danach werden alle ausstehenden Ereignisse als in einer Zusammenfassung enthalten markiert.

```yaml
service: connection_observer.send_summary_now
```

---

### `connection_observer.clear_history`

Löscht alle gespeicherten Ereignisse aus Speicher und persistentem Storage. Entfernt außerdem alle offenen HA-Reparatureinträge.

> ⚠️ Diese Aktion ist nicht rückgängig zu machen.

```yaml
service: connection_observer.clear_history
```

---

### `connection_observer.clear_device`

Entfernt alle gespeicherten Verbindungsabbruch-Ereignisse für ein **einzelnes Gerät** und löst einen offenen HA-Reparatureintrag dafür auf. Alle anderen Geräte bleiben unberührt.

Als Ziel wird eine beliebige Entität des Geräts angegeben.

**Wann sinnvoll:**
- Nach einer geplanten Wartung an einem bestimmten Gerät
- Um ein veraltetes Offline-Ereignis für ein einzelnes Gerät manuell zu schließen, ohne die gesamte History zu löschen

```yaml
service: connection_observer.clear_device
data:
  entity_id: light.wohnzimmer_lampe
```

---

## 10. Benachrichtigungsformate

### Sofortbenachrichtigung

**Einfach:**
> **Verbindungsabbruch**
> ⚠️ Wohnzimmer Steckdose (shelly) hat um 14:32 die Verbindung verloren.

**Mit Raum und Geräteinformationen:**
> **Verbindungsabbruch**
> ⚠️ Wohnzimmer Steckdose (shelly) hat um 14:32 die Verbindung verloren.
> 📍 Wohnzimmer  ·  Shelly Plus 1PM

### Wiederverbindungsbenachrichtigung (opt-in)

> **Verbindung wiederhergestellt**
> ✅ Wohnzimmer Steckdose ist wieder online.

### Sammelbenachrichtigung bei gleichzeitigen Ausfällen (≥ 5 Geräte)

Gehen 5 oder mehr Geräte innerhalb von 5 Sekunden offline, wird statt Einzelmeldungen eine einzige Sammelbenachrichtigung gesendet. Das verhindert eine Benachrichtigungsflut bei Router-Neustarts oder kurzen Infrastrukturausfällen.

**Verbindungsausfall:**
> **Verbindungsausfall – 8 Geräte**
> ⚠️ 8 Geräte gleichzeitig offline — vermutlich ein Infrastruktur-Problem (z. B. Router-Neustart).
> • Wohnzimmer Steckdose (shelly)
> • Küchen-Sensor (zha)
> • Flurlampe (hue)
> • Schlafzimmer Birne (hue)
> • Büro Schalter (esphome)
> • …

**Wiederverbindung:**
> **Verbindung wiederhergestellt – 8 Geräte**
> ✅ 8 Geräte wieder online:
> • Wohnzimmer Steckdose
> • Küchen-Sensor
> • Flurlampe
> • Schlafzimmer Birne
> • Büro Schalter
> • …

Sind weniger als 5 Geräte betroffen, werden weiterhin normale Einzelbenachrichtigungen gesendet (inkl. Cooldown-Prüfung).

### Zusammenfassung

> **Verbindungs-Zusammenfassung**
> 📋 3 Gerät(e) seit der letzten Zusammenfassung betroffen:
> • Küchen-Sensor [Küche] (zha): offline seit 19.05. 07:15, wieder online um 07:42
> • Schlafzimmer Birne [Schlafzimmer] (hue): offline seit 19.05. 09:05 ⚠️ noch offline
> • Flur Bewegungsmelder (esphome): offline seit 19.05. 11:20, wieder online um 11:28

---

## 11. Fortgeschrittene Anwendungsfälle

### Sofort- und Zusammenfassungsmodus gleichzeitig

Aktiviere beide Modi gleichzeitig:
- **Verzögerung** auf 3–5 Minuten setzen, damit kurze Aussetzer ignoriert werden
- **Sofortbenachrichtigung** für Echtzeit-Benachrichtigungen aktivieren
- **Zusammenfassung** für den täglichen Überblick aktivieren
- **Mindestausfallzeit** auf 5 Minuten setzen

### Kombination mit HA-Automatisierungen

```yaml
# Offline-Geräte per TTS ankündigen, wenn sie um 22 Uhr noch offline sind
trigger:
  - platform: time
    at: "22:00:00"
condition:
  - condition: state
    entity_id: binary_sensor.connection_observer_connection_problem
    state: "on"
action:
  - service: tts.speak
    data:
      message: >
        Achtung: {{ states('sensor.connection_observer_offline_devices') }}
        Gerät(e) sind aktuell offline.
```

### An mehrere Dienste senden

Wähle mehrere Dienste im Benachrichtigungsdienst-Feld aus. Alle Dienste erhalten jede Benachrichtigung gleichzeitig.

### Gerät ausschließen

Füge es zur Liste *Ausgeschlossene Geräte* in den Erweitert-Einstellungen hinzu. Alle Entitäten des Geräts werden dann ignoriert. Ist das Gerät zum Zeitpunkt des Speicherns offline, wird es sofort aus der Offline-Liste entfernt und ein offener HA-Reparatureintrag automatisch aufgelöst.

---

## 12. Fehlerbehebung

### Keine Benachrichtigungen werden gesendet

1. Prüfe, ob ein Benachrichtigungsdienst unter **Konfigurieren** ausgewählt ist.
2. Teste den Dienst direkt über **Entwicklerwerkzeuge → Dienste**.
3. Überprüfe das HA-Protokoll auf `connection_observer`-Fehler.
4. Stelle sicher, dass **Sofortbenachrichtigung** oder **Geplante Zusammenfassung** aktiviert ist.

### Die Zusammenfassung wird nicht gesendet

1. Prüfe, ob **Geplante Zusammenfassung** aktiviert ist.
2. Prüfe Uhrzeit und Tage unter **Konfigurieren**.
3. Prüfe `sensor.connection_observer_pending_summary_events` — ist er 0, gibt es keine ausstehenden Ereignisse und es wird keine Zusammenfassung gesendet.
4. Überprüfe das HA-Protokoll.

### Geräte werden nach HA-Neustart als offline angezeigt

Das sollte durch die 60-Sekunden-Startschutzzeit nicht passieren. Falls doch:
- Das Gerät ist möglicherweise tatsächlich offline.
- Wenn der Status in HA nicht `unavailable` ist, wird der Watchdog das Ereignis innerhalb von 5 Minuten korrigieren.

### Ein Gerät wird als offline angezeigt, ist aber erreichbar

Der Watchdog läuft alle 5 Minuten und schließt das Ereignis automatisch ab. Du kannst auch `clear_history` aufrufen, um sofort zurückzusetzen.

### Der HA-Reparatureintrag wurde nicht erstellt

1. Prüfe, ob **HA-Reparaturen-Eintrag nach N Stunden offline** nicht auf `0` gesetzt ist.
2. Das Gerät muss länger als den Schwellwert offline sein. Der Watchdog erstellt den Eintrag bei seinem nächsten Lauf (alle 5 Minuten), daher kann es kurz nach dem Überschreiten des Schwellwerts noch einen Moment dauern.

---

## 13. Bekannte Einschränkungen

- **Nur-Cloud-Integrationen:** Geräte, die ausschließlich über einen Cloud-Dienst verbunden sind, werden möglicherweise nicht erkannt, wenn die Integration bei fehlender Cloud-Verbindung keinen `unavailable`-Status setzt.
- **Polling-Integrationen:** Eine Verbindungsunterbrechung wird erst nach dem nächsten Abfragezyklus erkannt, was zu einer kurzen Verzögerung führen kann.
- **Passive BLE-Geräte (BTHome etc.):** Bluetooth-Low-Energy-Sensoren wie BTHome-Tür-/Fenstersensoren halten keine dauerhafte Verbindung — sie senden periodische Advertisements. Geht ein solches Gerät offline (z. B. Batterie entfernt), setzt Home Assistant die Entitäten erst nach seinem eigenen internen Timeout auf `unavailable` — das kann mehrere Stunden dauern. Connection Observer kann erst reagieren, wenn HA `unavailable` meldet. Echtzeitüberwachung ist bei passiven BLE-Geräten daher strukturell nicht möglich. Sie unterscheiden sich grundlegend von WLAN-Geräten.
- **Zigbee2MQTT – Verfügbarkeitsprüfung erforderlich:** Connection Observer reagiert auf den `unavailable`-Status von Entitäten. Zigbee2MQTT setzt diesen Status standardmäßig **nicht** — die Verfügbarkeitsprüfung muss in Z2M aktiviert werden: **Einstellungen → Verfügbarkeit → aktiviert**. Ohne diese Einstellung werden Z2M-Geräte nicht erkannt.
- **Nur eine Instanz:** Connection Observer unterstützt eine einzige Integrationsinstanz pro HA-Installation.
- **30-Tage-Ereignisaufbewahrung:** Ereignisse, die älter als 30 Tage sind, werden automatisch aus dem Speicher entfernt.
