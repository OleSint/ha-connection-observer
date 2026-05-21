# Connection Observer – Dokumentation

**Version:** 1.0.1  
**Repository:** [github.com/OleSint/ha-connection-observer](https://github.com/OleSint/ha-connection-observer)

---

## Inhaltsverzeichnis

1. [Was ist Connection Observer?](#1-was-ist-connection-observer)
2. [Funktionsprinzip](#2-funktionsprinzip)
3. [Installation](#3-installation)
4. [Setup-Assistent](#4-setup-assistent)
5. [Konfigurationsoptionen](#5-konfigurationsoptionen)
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

Der Setup-Assistent führt dich durch vier Schritte. Alle Einstellungen können anschließend über den **Konfigurieren**-Button der Integrationskarte geändert werden.

### Schritt 1 – Protokolle

**Was du hier auswählst, legt fest, welche Geräte überwacht werden.**

Der Assistent zeigt nur Integrationsfamilien an, die in deiner HA-Instanz tatsächlich eingerichtet sind.

| Feld | Beschreibung |
|---|---|
| **Zu überwachende Protokolle** | Mehrfachauswahl. Wähle eine oder mehrere Integrationsfamilien aus. |
| **Benachrichtigungssprache** | Wähle Englisch, Deutsch, Français, Nederlands oder Español. |

> **Tipp:** Du kannst Protokolle jederzeit hinzufügen oder entfernen. Neu hinzugefügte Geräte eines ausgewählten Protokolls werden automatisch erfasst.

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

| Feld | Beschreibung |
|---|---|
| **Verzögerung** | Minuten offline, bevor ein Ereignis erstellt wird. Standard: **0** (sofort). |
| **Cooldown** | Mindestabstand zwischen Sofortbenachrichtigungen pro Gerät. Standard: **0** (kein Limit). |
| **Mindestausfallzeit für Zusammenfassung** | Ereignisse kürzer als dieser Wert erscheinen nicht in der Zusammenfassung. Standard: **0** (alle Ereignisse). |
| **Raum / Bereich anzeigen** | HA-Bereichsname in Benachrichtigungen einblenden. Standard: **aus**. |
| **Hersteller & Modell anzeigen** | Geräteinformationen in Sofortmeldungen einblenden. Standard: **aus**. |
| **Ausgeschlossene Entitätsdomänen** | Ganze Entitätsdomänen von der Überwachung ausschließen (z. B. `sensor`, `button`). Aus der Liste auswählen oder eigene Domäne eingeben. `device_tracker`-Entitäten werden immer automatisch ignoriert und müssen hier nicht eingetragen werden. |
| **Ausgeschlossene Entitäten** | Liste von Entitäten, die von der Überwachung ausgenommen werden. |

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

### Empfohlene Startkonfiguration

- **Sofortbenachrichtigung:** aus
- **Zusammenfassung:** ein, täglich um 08:00 Uhr
- **Verzögerung:** 5 Minuten (vermeidet Fehlalarme durch kurze WLAN-Aussetzer)
- **Mindestausfallzeit:** 5 Minuten (hält die Zusammenfassung übersichtlich)
- **Bereich anzeigen:** ein (macht Benachrichtigungen deutlich lesbarer)
- **HA-Reparaturen-Schwellwert:** 24 Stunden

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
| `devices` | Liste der Gerätenamen, die aktuell offline sind. |

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

### Entität ausschließen

Füge sie zur Liste *Ausgeschlossene Entitäten* in den Erweitert-Einstellungen hinzu. Die anderen Entitäten des Geräts werden weiter überwacht.

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
- **Bluetooth-Abdeckung:** Geräte, die nur auf der Ebene des rohen Bluetooth-Adapters sichtbar sind, werden möglicherweise nicht abgedeckt.
- **Nur eine Instanz:** Connection Observer unterstützt eine einzige Integrationsinstanz pro HA-Installation.
- **30-Tage-Ereignisaufbewahrung:** Ereignisse, die älter als 30 Tage sind, werden automatisch aus dem Speicher entfernt.
