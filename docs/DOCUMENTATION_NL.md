# Connection Observer – Documentatie (Nederlands)

**Versie:** 1.0.1  
**Repository:** [github.com/OleSint/ha-connection-observer](https://github.com/OleSint/ha-connection-observer)

---

## Inhoudsopgave

1. [Wat is Connection Observer?](#1-wat-is-connection-observer)
2. [Hoe het werkt](#2-hoe-het-werkt)
3. [Installatie](#3-installatie)
4. [Installatiewizard](#4-installatiewizard)
5. [Configuratieopties](#5-configuratieopties)
6. [Meldingssjablonen](#6-meldingssjablonen)
7. [HA Repairs integratie](#7-ha-repairs-integratie)
8. [Entiteiten](#8-entiteiten)
9. [Services](#9-services)
10. [Meldingsformaten](#10-meldingsformaten)
11. [Geavanceerde gebruiksscenario's](#11-geavanceerde-gebruiksscenarios)
12. [Probleemoplossing](#12-probleemoplossing)
13. [Bekende beperkingen](#13-bekende-beperkingen)

---

## 1. Wat is Connection Observer?

Connection Observer is een aangepaste Home Assistant integratie die continu de verbindingen van je slimme thuisapparaten bewaakt en je waarschuwt wanneer iets offline gaat — voordat je zelf merkt dat een lichtschakelaar niet meer reageert of een sensor geen waarden meer stuurt.

**Het kernidee** is bewaking per *protocolfamilie* in plaats van per individuele entiteit. In plaats van 200 entiteiten één voor één te selecteren, kies je eenvoudig "bewaak alle Zigbee-apparaten" of "bewaak alle ESPHome-apparaten". Elk apparaat dat tot die integratifamilie behoort wordt automatisch meegenomen — ook nieuwe apparaten die je later toevoegt.

---

## 2. Hoe het werkt

### De `unavailable`-status

Home Assistant heeft een ingebouwd mechanisme om aan te geven dat een apparaat niet meer bereikbaar is: het zet alle entiteiten van dat apparaat op de status `unavailable`. Dit gebeurt automatisch wanneer:

- Een Zigbee- of Z-Wave-apparaat niet meer reageert op de coördinator
- Een WiFi-apparaat (ESPHome, Shelly, etc.) niet meer bereikbaar is op het netwerk
- Een Hue-lamp aan de muur wordt uitgeschakeld en de bridge het contact verliest
- Een andere integratie detecteert dat de communicatie is verbroken

Connection Observer luistert naar precies deze overgang: van welke status dan ook → `unavailable`. Wanneer dit wordt gedetecteerd, wordt een *verbindingsverbreking* aangemaakt voor het betrokken apparaat.

### Deduplicatie op apparaatniveau

De meeste apparaten hebben meerdere entiteiten in Home Assistant. Een Zigbee-stekker kan entiteiten hebben voor de schakelstatus, huidig verbruik, totale energie, spanning, enzovoort. Wanneer die stekker offline gaat, worden alle entiteiten tegelijk `unavailable`.

Connection Observer bepaalt via het HA-apparaatregister bij welk *apparaat* een entiteit hoort, en maakt slechts **één gebeurtenis per apparaat** aan — ongeacht hoeveel entiteiten het heeft. Dat betekent één melding per apparaat, niet vijf.

### Opstartbeveiliging

Wanneer Home Assistant herstart, hebben alle integraties even nodig om hun apparaten opnieuw te verbinden. Tijdens dit venster gaan veel entiteiten kort door `unavailable`. Connection Observer wacht 60 seconden na het volledig opstarten van HA voordat het verbrekingen begint bij te houden. Dit voorkomt een stroom van valse alarmen bij elke herstart.

### Permanente opslag

Alle verbrekingsgebeurtenissen worden opgeslagen in het ingebouwde opslagsysteem van HA (`~/.homeassistant/.storage/`). Gebeurtenissen overleven herstarts en worden tot 30 dagen bewaard.

### Waakhond (Watchdog)

Elke 5 minuten controleert Connection Observer actief of apparaten met open verbrekingen inderdaad nog steeds niet bereikbaar zijn. Als een apparaat terug online is gekomen zonder een `state_changed`-event te produceren, detecteert de watchdog dit en sluit de gebeurtenis.

---

## 3. Installatie

### Via HACS (aanbevolen)

1. Zorg dat HACS geïnstalleerd is. Volg anders de [HACS-installatiehandleiding](https://hacs.xyz/docs/setup/download).
2. Open **HACS → Integraties** in de HA-zijbalk.
3. Klik op het **menu met drie punten** (rechtsboven) → **Aangepaste opslagplaatsen**.
4. Voer `https://github.com/OleSint/ha-connection-observer` in als URL en selecteer **Integratie** als categorie. Klik op **Toevoegen**.
5. Zoek naar **Connection Observer** in de HACS-lijst en klik op **Downloaden**.
6. **Herstart Home Assistant.**
7. Ga na de herstart naar **Instellingen → Apparaten en diensten → Integratie toevoegen** en zoek naar **Connection Observer**.

### Handmatige installatie

1. Download de nieuwste versie van de [GitHub-releasepagina](https://github.com/OleSint/ha-connection-observer/releases).
2. Pak het archief uit en kopieer de map `custom_components/connection_observer` naar je HA-configuratiemap onder `config/custom_components/connection_observer`.
3. **Herstart Home Assistant.**
4. Ga na de herstart naar **Instellingen → Apparaten en diensten → Integratie toevoegen** en zoek naar **Connection Observer**.

---

## 4. Installatiewizard

De installatiewizard leidt je door vier stappen. Alle instellingen kunnen achteraf worden gewijzigd via de knop **Configureren** op de integratiekaart.

### Stap 1 – Protocollen

**Wat je hier selecteert, bepaalt welke apparaten worden bewaakt.**

De wizard toont alleen integratifamilies die daadwerkelijk zijn geconfigureerd in jouw HA-instantie.

| Veld | Beschrijving |
|---|---|
| **Te bewaken protocollen** | Meervoudige selectie. Kies één of meer integratifamilies. |
| **Taal van meldingen** | Kies English, Deutsch, Français, Nederlands of Español. |

> **Tip:** Je kunt protocollen altijd later toevoegen of verwijderen. Nieuwe apparaten van een geselecteerd protocol worden automatisch meegenomen.

> **Zigbee2MQTT-gebruikers:** Zigbee2MQTT-apparaten verschijnen in HA onder het `mqtt`-integratiedomein — er is geen apart Zigbee2MQTT-item. Selecteer **MQTT** om ze te bewaken. Let op: dit omvat ook alle andere MQTT-gebaseerde apparaten in je installatie (bijv. Tasmota, eigen sensoren). Voor fijnere controle is labelgebaseerde filtering gepland voor een toekomstige versie.

### Stap 2 – Meldingen

**Stel in hoe en wanneer je waarschuwingen ontvangt.**

| Veld | Beschrijving |
|---|---|
| **Meldingsdienst(en)** | Meervoudige selectie. Kies één of meer `notify.*`-diensten. |
| **Directe melding bij verbindingsverlies** | Indien ingeschakeld, wordt direct een melding verzonden. Standaard: **uit**. |
| **Geplande samenvatting** | Indien ingeschakeld, wordt een samenvatting verstuurd op de ingestelde tijd. Standaard: **aan**. |
| **Tijd van samenvatting** | Tijdstip van de dag voor de samenvatting. |
| **Dagen van samenvatting** | Weekdagen waarop de samenvatting wordt verzonden. Standaard: elke dag. |
| **Melding bij herverbinding** | Opt-in. Melding wanneer een apparaat weer online komt. Standaard: **uit**. |

### Stap 3 – Test

Een optionele teststap stuurt een melding naar al je geselecteerde diensten om te controleren of alles correct werkt.

- Vink **Testmelding nu verzenden** aan (standaard aangevinkt) en klik op Verzenden.
- Vink het vakje uit om deze stap over te slaan.
- Als de test mislukt, wordt een foutmelding getoond. Je kunt het opnieuw proberen of het vakje uitvinken om toch verder te gaan.

### Stap 4 – Geavanceerd

**Alle velden zijn optioneel. De waarde 0 schakelt de betreffende functie uit.**

| Veld | Beschrijving |
|---|---|
| **Vertraging** | Minuten offline voordat een gebeurtenis wordt aangemaakt. Standaard: **0** (direct). |
| **Minimale tijd tussen meldingen** | Minimale tijd tussen directe meldingen per apparaat. Standaard: **0** (geen limiet). |
| **Minimale offline-duur** | Gebeurtenissen korter dan dit worden niet in de samenvatting opgenomen. Standaard: **0** (alle gebeurtenissen). |
| **Ruimte / zone opnemen** | HA-zonenaam weergeven in meldingen. Standaard: **uit**. |
| **Fabrikant & model opnemen** | Apparaatinformatie weergeven. Standaard: **uit**. |
| **Uitgesloten entiteitsdomeinen** | Sluit volledige entiteitsdomeinen uit (bijv. `sensor`, `button`). `device_tracker`-entiteiten worden altijd automatisch uitgesloten. |
| **Uitgesloten entiteiten** | Lijst van specifieke entiteiten die worden uitgesloten van bewaking. |

---

## 5. Configuratieopties

Alle instellingen van de wizard kunnen op elk moment worden gewijzigd via **Instellingen → Apparaten en diensten → Connection Observer → Configureren**.

Naast de wizard-instellingen biedt de optiepagina ook:

### Testmelding

Via de optiepagina kun je op elk moment een testmelding versturen zonder de integratie opnieuw te configureren. Vink **Testmelding nu verzenden** aan om een testbericht naar al je geconfigureerde diensten te sturen voordat de nieuwe instellingen worden opgeslagen.

### Uitgesloten entiteitsdomeinen

Je kunt volledige entiteitsdomeinen uitsluiten van bewaking — bijv. `sensor`, `button`, `number`. Dit is handig wanneer bepaalde domeinen in jouw opzet altijd tijdelijk `unavailable` worden. `device_tracker`-entiteiten worden altijd automatisch uitgesloten, ongeacht deze instelling.

### HA Repairs drempelwaarde

Stelt het aantal uren in dat een apparaat offline moet zijn voordat er een permanent probleem wordt aangemaakt onder **Instellingen → Reparaties**. De waarde `0` schakelt deze functie uit. Standaard: **24 uur**.

Zie [Sectie 7](#7-ha-repairs-integratie) voor details.

### Meldingssjablonen

Zeven optionele tekstvelden waarmee je het formaat van elke melding kunt aanpassen. Laat een veld leeg om de taalstandaard te gebruiken.

Zie [Sectie 6](#6-meldingssjablonen) voor details.

### Aanbevolen beginconfiguratie

- **Directe melding:** uit
- **Samenvatting:** aan, dagelijks om 08:00
- **Vertraging:** 5 minuten (vermijdt valse alarmen door korte WiFi-uitval)
- **Minimale offline-duur:** 5 minuten (houdt de samenvatting overzichtelijk)
- **Zone opnemen:** aan (maakt meldingen veel leesbaarder)
- **HA Repairs drempelwaarde:** 24 uur

---

## 6. Meldingssjablonen

Connection Observer verstuurt drie soorten meldingen: direct (verbreking), herverbinding en samenvatting. Elk type heeft een titel en een berichttekst die onafhankelijk van elkaar kunnen worden aangepast.

### Beschikbare sjablonen

Alle sjabloonvelden staan in **Instellingen → Apparaten en diensten → Connection Observer → Configureren**, onderaan de optiepagina.

| Sjabloonsleutel | Van toepassing op | Beschikbare variabelen |
|---|---|---|
| `tmpl_imm_title` | Directe melding – titel | `{device_name}` `{protocol}` `{time}` `{area}` `{model}` |
| `tmpl_imm_msg` | Directe melding – bericht | `{device_name}` `{protocol}` `{time}` `{area}` `{model}` |
| `tmpl_rec_title` | Herverbinding – titel | `{device_name}` |
| `tmpl_rec_msg` | Herverbinding – bericht | `{device_name}` |
| `tmpl_sum_title` | Samenvatting – titel | `{count}` |
| `tmpl_sum_resolved` | Samenvatting – regel voor opgelost | `{device_name}` `{area}` `{protocol}` `{time_offline}` `{time_online}` |
| `tmpl_sum_ongoing` | Samenvatting – regel voor nog offline | `{device_name}` `{area}` `{protocol}` `{time_offline}` |

### Opmerkingen over variabelen

- `{area}` is voorgeformatteerd als ` [Ruimtenaam]` (met een voorafgaande spatie) wanneer de optie *ruimte opnemen* is ingeschakeld, of als lege tekenreeks.
- `{model}` is `Fabrikant – Model` of leeg.
- `{time}` / `{time_offline}` / `{time_online}` zijn in het formaat `HH:MM`. Voor `{time_offline}` in de samenvatting is de datum inbegrepen als `MM/DD HH:MM`.

### Belangrijke opmerkingen

- Als je een aangepaste `tmpl_imm_msg` instelt, wordt de automatische tweede regel met zone en model (📍 …) **niet** toegevoegd. Voeg `{area}` en `{model}` toe aan je sjabloon als je die informatie wilt.
- Sjabloonfouten (bijv. een typefout in een variabelenaam) worden als waarschuwingen geregistreerd.

---

## 7. HA Repairs integratie

Wanneer een apparaat langer offline is dan de geconfigureerde drempelwaarde (standaard: 24 uur), maakt Connection Observer een permanent probleem aan onder **Instellingen → Reparaties**. Dit is een aanvulling op de reguliere meldingen.

### Wat het probleem toont

Het probleem geeft aan:
- De naam van het apparaat
- Het protocol / de integratie
- Het tijdstip waarop het offline ging

### Automatische oplossing

Wanneer het apparaat weer online komt — via een `state_changed`-event of via de watchdog — wordt het probleem **automatisch verwijderd**.

### Uitschakelen

Stel **HA Repairs-melding na N uur offline** in op `0` in de opties.

---

## 8. Entiteiten

Connection Observer maakt drie entiteiten aan per integratie-instantie.

### `sensor.connection_observer_offline_devices`

**Type:** Sensor | **Eenheid:** devices | **Pictogram:** `mdi:lan-disconnect`

Toont het aantal apparaten dat momenteel offline is.

**Toestandsattributen:**

| Attribuut | Beschrijving |
|---|---|
| `devices` | Vlakke lijst van apparaatnamen die momenteel offline zijn. |
| `by_protocol` | Uitsplitsing per protocol: aantal offline en gedetailleerde apparaatlijst per integratiefamilie. |

Het attribuut `by_protocol` heeft de volgende structuur:

```yaml
by_protocol:
  shelly:
    offline: 1
    devices:
      - name: "Stekker Keuken"
        offline_since: "22.05. 14:30"
        offline_duration: "2h 15m"
  bthome:
    offline: 0
    devices: []
```

Alleen protocollen met ten minste één momenteel offline apparaat verschijnen in dit attribuut.

**Voorbeeld — Markdown-kaart met protocollenstatus:**
```yaml
type: markdown
content: >
  {% set proto = state_attr('sensor.connection_observer_offline_devices', 'by_protocol') %}
  {% for p, data in proto.items() %}
  **{{ p }}**: {{ data.devices | map(attribute='name') | join(', ') }}
  (offline sinds {{ data.devices[0].offline_since }})
  {% endfor %}
```

**Voorbeeld in een automatisering:**
```yaml
condition:
  - condition: numeric_state
    entity_id: sensor.connection_observer_offline_devices
    above: 0
```

---

### `sensor.connection_observer_pending_summary_events`

**Type:** Sensor | **Eenheid:** events | **Pictogram:** `mdi:clock-alert-outline`

Toont het aantal verbrekingsgebeurtenissen dat nog niet in een samenvatting is opgenomen. Wordt gereset naar 0 na het verzenden van een samenvatting of na `clear_history`.

---

### `binary_sensor.connection_observer_connection_problem`

**Type:** Binaire sensor | **Klasse:** `problem` | **Pictogram:** `mdi:check-network`

- **`AAN`** – minstens één apparaat is momenteel offline
- **`UIT`** – alle bewaakte apparaten zijn bereikbaar

**Voorbeeld – waarschuwing als het probleem langer dan 10 minuten aanhoudt:**
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
      message: "Een apparaat is al meer dan 10 minuten offline!"
```

---

## 9. Services

### `connection_observer.send_summary_now`

Verstuurt onmiddellijk een samenvatting van alle openstaande verbrekingsgebeurtenissen. Na het aanroepen worden alle openstaande gebeurtenissen gemarkeerd als opgenomen in een samenvatting.

```yaml
service: connection_observer.send_summary_now
```

---

### `connection_observer.clear_history`

Wist alle opgeslagen gebeurtenissen uit geheugen en permanente opslag. Verwijdert ook alle openstaande HA Repairs-items.

> ⚠️ Deze actie kan niet ongedaan worden gemaakt.

```yaml
service: connection_observer.clear_history
```

---

### `connection_observer.clear_device`

Wist alle opgeslagen verbrekingsgebeurtenissen voor één specifiek apparaat en verwijdert het bijbehorende HA Repairs-item. Nuttig als een apparaat is vervangen of als je de geschiedenis van één enkel apparaat wilt resetten zonder de volledige geschiedenis te wissen.

| Parameter | Beschrijving |
|---|---|
| `entity_id` | Verplicht. Een entiteit-ID van het te resetten apparaat (bijv. `sensor.woonkamer_stekker_energy`). |

```yaml
service: connection_observer.clear_device
data:
  entity_id: sensor.woonkamer_stekker_energy
```

---

## 10. Meldingsformaten

### Directe melding

**Eenvoudig:**
> **Verbinding verbroken**
> ⚠️ Woonkamer Stekker (shelly) heeft om 14:32 de verbinding verbroken.

**Met zone en apparaatinformatie ingeschakeld:**
> **Verbinding verbroken**
> ⚠️ Woonkamer Stekker (shelly) heeft om 14:32 de verbinding verbroken.
> 📍 Woonkamer  ·  Shelly Plus 1PM

### Herverbindingsmelding (opt-in)

> **Verbinding hersteld**
> ✅ Woonkamer Stekker is weer online.

### Samenvatting

> **Verbindingsoverzicht**
> 📋 3 apparaat/apparaten getroffen sinds het laatste overzicht:
> • Keuken Sensor [Keuken] (zha): offline sinds 05/19 07:15, weer online om 07:42
> • Slaapkamer Lamp [Slaapkamer] (hue): offline sinds 05/19 09:05 ⚠️ nog steeds offline
> • Gang Bewegingssensor (esphome): offline sinds 05/19 11:20, weer online om 11:28

---

## 11. Geavanceerde gebruiksscenario's

### Direct en samenvatting tegelijk gebruiken

Schakel beide modi in:
- **Vertraging** van 3–5 minuten om korte uitval te negeren
- **Directe melding** voor realtime bewustzijn
- **Samenvatting** voor een dagelijks overzicht
- **Minimale offline-duur** van 5 minuten om alleen betekenisvolle gebeurtenissen te tonen

### Combineren met HA-automatiseringen

```yaml
# Offline apparaten via TTS aankondigen als ze om 22 uur nog offline zijn
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
        Let op: {{ states('sensor.connection_observer_offline_devices') }}
        apparaat/apparaten zijn momenteel offline.
```

### Naar meerdere diensten sturen

Selecteer meerdere diensten in het meldingsdienstveld. Alle diensten ontvangen elke melding tegelijkertijd.

### Een specifieke entiteit uitsluiten

Voeg deze toe aan de lijst *Uitgesloten entiteiten* in de geavanceerde instellingen. De andere entiteiten van het apparaat blijven bewaakt.

---

## 12. Probleemoplossing

### Er worden geen meldingen verstuurd

1. Controleer of er een meldingsdienst is geselecteerd onder **Configureren**.
2. Test je notify-dienst direct via **Ontwikkelaarstools → Diensten**.
3. Bekijk het HA-logboek op `connection_observer`-fouten.
4. Zorg dat **Directe melding** of **Geplande samenvatting** is ingeschakeld.

### De samenvatting wordt niet verstuurd

1. Controleer of **Geplande samenvatting** is ingeschakeld.
2. Controleer het tijdstip en de dagen onder **Configureren**.
3. Controleer `sensor.connection_observer_pending_summary_events` — als deze 0 is, zijn er geen openstaande gebeurtenissen.
4. Bekijk het HA-logboek.

### Apparaten worden na een HA-herstart als offline weergegeven

Dit zou niet mogen gebeuren vanwege de opstartbeschermingsperiode van 60 seconden. Als het toch gebeurt:
- Het apparaat is mogelijk echt offline.
- Als de status in HA niet `unavailable` is, corrigeert de watchdog de gebeurtenis binnen 5 minuten.

### Een apparaat wordt als offline weergegeven maar is bereikbaar in HA

De watchdog draait elke 5 minuten en sluit de gebeurtenis automatisch. Je kunt ook `clear_history` aanroepen om onmiddellijk te resetten.

### Het HA Repairs-item is niet aangemaakt

1. Controleer of de drempelwaarde niet op `0` staat.
2. Het apparaat moet langer dan de drempelwaarde offline zijn. De watchdog maakt het item aan bij zijn volgende uitvoering (elke 5 minuten).

---

## 13. Bekende beperkingen

- **Alleen-cloud integraties:** Apparaten die uitsluitend via een clouddienst verbinden, worden mogelijk niet gedetecteerd als de integratie geen `unavailable`-status instelt bij cloudproblemen.
- **Poll-integraties:** Een verbreking wordt pas gedetecteerd na de volgende pollcyclus.
- **Passieve BLE-apparaten (BTHome etc.):** Bluetooth Low Energy-sensoren zoals BTHome deur-/raamsensoren onderhouden geen persistente verbinding — ze zenden periodieke berichten uit. Als zo'n apparaat offline gaat (bijv. batterij verwijderd), stelt Home Assistant de entiteiten pas op `unavailable` na een eigen interne time-out, die enkele uren kan bedragen. Connection Observer kan pas reageren zodra HA `unavailable` meldt. Realtime bewaking is voor passieve BLE-apparaten structureel niet mogelijk, in tegenstelling tot WiFi-apparaten.
- **Slechts één instantie:** Connection Observer ondersteunt één integratie-instantie per HA-installatie.
- **30 dagen bewaring:** Gebeurtenissen ouder dan 30 dagen worden automatisch verwijderd.
