# Connection Observer – Documentatie (Nederlands)

**Versie:** 1.2.0  
**Repository:** [github.com/OleSint/ha-connection-observer](https://github.com/OleSint/ha-connection-observer)

---

## Inhoudsopgave

1. [Wat is Connection Observer?](#1-wat-is-connection-observer)
2. [Hoe het werkt](#2-hoe-het-werkt)
3. [Installatie](#3-installatie)
4. [Installatiewizard](#4-installatiewizard)
5. [Configuratieopties](#5-configuratieopties)
   - [Vertragingen per protocol](#vertragingen-per-protocol)
   - [Watch label – aangepaste offline-indicatoren](#watch-label--aangepaste-offline-indicatoren)
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

De installatiewizard leidt je door vijf stappen. Alle instellingen kunnen achteraf worden gewijzigd via de knop **Configureren** op de integratiekaart.

### Stap 1 – Protocollen

**Wat je hier selecteert, bepaalt welke apparaten worden bewaakt.**

De wizard toont alleen integratifamilies die daadwerkelijk zijn geconfigureerd in jouw HA-instantie.

| Veld | Beschrijving |
|---|---|
| **Te bewaken protocollen** | Meervoudige selectie. Kies één of meer integratifamilies. |
| **Taal van meldingen** | Kies English, Deutsch, Français, Nederlands of Español. |

> **Tip:** Je kunt protocollen altijd later toevoegen of verwijderen. Nieuwe apparaten van een geselecteerd protocol worden automatisch meegenomen.

> **Zigbee2MQTT-gebruikers:** Zigbee2MQTT-apparaten verschijnen in HA onder het `mqtt`-integratiedomein — er is geen apart Zigbee2MQTT-item. Selecteer **MQTT** om ze te bewaken. Let op: dit omvat ook alle andere MQTT-gebaseerde apparaten in je installatie (bijv. Tasmota, eigen sensoren). Voor fijnere controle is labelgebaseerde filtering gepland voor een toekomstige versie.

> ⚠️ **Belangrijk:** Connection Observer kan apparaten alleen detecteren wanneer HA ze op `unavailable` zet. Zigbee2MQTT doet dit standaard **niet** — beschikbaarheidscontroles moeten eerst worden ingeschakeld: **Zigbee2MQTT → Instellingen → Beschikbaarheid → ingeschakeld**. Zonder deze instelling kan Connection Observer Z2M-apparaten niet detecteren.

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
De **globale vertraging** die hier wordt ingesteld, geldt voor alle protocollen, tenzij er in Stap 5 een specifieke vertraging per protocol is ingesteld.

| Veld | Beschrijving |
|---|---|
| **Vertraging** | Minuten offline voordat een gebeurtenis wordt aangemaakt. Standaard: **0** (direct). |
| **Minimale tijd tussen meldingen** | Minimale tijd tussen directe meldingen per apparaat. Standaard: **0** (geen limiet). |
| **Minimale offline-duur** | Gebeurtenissen korter dan dit worden niet in de samenvatting opgenomen. Standaard: **0** (alle gebeurtenissen). |
| **Ruimte / zone opnemen** | HA-zonenaam weergeven in meldingen. Standaard: **uit**. |
| **Fabrikant & model opnemen** | Apparaatinformatie weergeven. Standaard: **uit**. |
| **Uitgesloten entiteitsdomeinen** | Sluit volledige entiteitsdomeinen uit (bijv. `sensor`, `button`). `device_tracker`-entiteiten worden altijd automatisch uitgesloten. |
| **Uitgesloten apparaten** | Lijst van specifieke apparaten die volledig worden uitgesloten van bewaking. Alleen apparaten met minimaal één entiteit op een geconfigureerd protocol worden getoond — virtuele services (HACS, Supervisor, Add-ons, etc.) verschijnen niet. Wordt een apparaat uitgesloten terwijl het offline is, dan wordt het direct uit de offline-lijst verwijderd en een openstaand HA Repairs-probleem automatisch opgelost. |

### Stap 5 – Expert

**Beide functies zijn optioneel. Sla deze stap over als je alleen de globale vertraging nodig hebt.**

#### Vertragingen per protocol

Elk protocol dat je in Stap 1 hebt geselecteerd, verschijnt hier met een eigen vertragingsveld. Een waarde van **0** betekent "gebruik de globale vertraging uit Stap 4". Voer een positieve waarde in om de globale vertraging voor dat specifieke protocol te overschrijven.

**Tip: Aanbevolen vertragingen toepassen**  
Vink **Aanbevolen vertragingen toepassen voor alle protocollen** aan en klik op Verzenden. Alle vertragingsvelden worden automatisch ingevuld met de aanbevolen waarden. Je kunt de waarden daarna individueel aanpassen of ze zo accepteren.

Aanbevolen waarden zijn gebaseerd op de typische verbindingskarakteristieken van elke protocolfamilie:
- Directe TCP-protocollen (ESPHome, Shelly, Tasmota) → **2 min** (persistente verbinding, snelle detectie)
- Lokale mesh-protocollen (ZHA, Z-Wave JS) → **5 min** (mesh-omleiding kost even tijd)
- Passieve BLE (BTHome, GARDENA Bluetooth) → **20 min** (zeldzame advertentiecycli)
- Cloudprotocollen (Tuya, Nest, Ring…) → **10 min** (pollingslatentie)

Zie de [volledige referentietabel](#vertragingen-per-protocol) in Sectie 5 voor alle waarden.

#### Watch label – aangepaste offline-indicatoren

Voer hier de naam van een HA-label in (bijv. `offline_indicator`). Elke entiteit waaraan je dit label toewijst via de HA-labeleditor, wordt door Connection Observer behandeld als een aangepaste offline-indicator:

- Wanneer de toestand van de entiteit **`on`** wordt → maakt Connection Observer een offline-gebeurtenis aan (protocol weergegeven als `custom`)
- Wanneer de toestand van de entiteit **`off`** wordt → markeert Connection Observer het apparaat als weer online

Deze functie is bewust generiek: label elke gewenste entiteit — een template binaire sensor, een helper of een andere binaire entiteit — en Connection Observer reageert op de statuswijzigingen.

**Typisch gebruik:** passieve BLE-apparaten (BTHome-sensoren, GARDENA Bluetooth) kunnen niet in realtime worden bewaakt via de `unavailable`-status. Zie [Bekende beperkingen](#13-bekende-beperkingen) en het [Watch label](#watch-label--aangepaste-offline-indicatoren) in Sectie 5 voor een volledig stapsgewijs voorbeeld.

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

### Vertragingen per protocol

Elk geselecteerd protocol kan een eigen vertraging hebben die de globale waarde overschrijft. Stel de vertraging van een protocol in op **0** (of laat het leeg) om terug te vallen op de globale vertraging.

**Instellen met één klik:** Vink in de Expert-stap (wizard) of Expert-pagina (opties) **Aanbevolen vertragingen toepassen** aan en klik op Verzenden. Alle velden worden automatisch ingevuld.

| Protocol | Domein | Aanbevolen vertraging | Reden |
|---|---|---:|---|
| Zigbee (ZHA) | `zha` | 5 min | Mesh-omleiding kost even tijd |
| Zigbee (deCONZ) | `deconz` | 5 min | Mesh-omleiding kost even tijd |
| Z-Wave (Z-Wave JS) | `zwave_js` | 5 min | Mesh-omleiding kost even tijd |
| Matter | `matter` | 5 min | Mesh-achtig gedrag |
| Thread (OTBR) | `otbr` | 5 min | Thread-mesh |
| Bluetooth | `bluetooth` | 10 min | BLE-verbinding is langzamer |
| BTHome | `bthome` | 20 min | Passieve BLE – zeldzame advertenties |
| RFXtrx (433 MHz) | `rfxtrx` | 10 min | Eénrichtings-RF, geen bevestiging |
| MySensors | `mysensors` | 10 min | Langzame polling |
| Insteon | `insteon` | 5 min | Eigen bus, pollinggebaseerd |
| KNX | `knx` | 5 min | Bedrade bus, betrouwbaar maar gepolled |
| Velbus | `velbus` | 5 min | Bedrade bus |
| ESPHome | `esphome` | 2 min | Persistente TCP, zeer snelle detectie |
| Shelly | `shelly` | 2 min | Persistente TCP, zeer snelle detectie |
| Tasmota | `tasmota` | 2 min | Persistente TCP, zeer snelle detectie |
| Tuya | `tuya` | 5 min | Cloudpolling |
| WLED | `wled` | 2 min | Lokale TCP |
| TP-Link (Kasa/Tapo) | `tplink` | 3 min | Lokale TCP |
| TP-Link Omada | `tplink_omada` | 3 min | Lokale TCP |
| Broadlink | `broadlink` | 3 min | Lokale TCP |
| Philips Hue | `hue` | 3 min | Lokale Hue-bridge |
| IKEA TRÅDFRI | `tradfri` | 5 min | IKEA-hub kan traag reageren |
| LIFX | `lifx` | 3 min | Lokale UDP/TCP |
| Nanoleaf | `nanoleaf` | 3 min | Lokale TCP |
| Yeelight | `yeelight` | 2 min | Lokale TCP |
| Xiaomi Mi Home | `xiaomi_miio` | 5 min | Lokaal + cloud gemengd |
| Sonos | `sonos` | 3 min | Lokaal netwerk |
| Google Cast | `cast` | 3 min | Lokaal netwerk |
| Logitech Media Server | `squeezebox` | 5 min | Serverafhankelijk |
| Kodi | `kodi` | 3 min | Lokaal netwerk |
| Plex | `plex` | 5 min | Serverafhankelijk |
| Sony Bravia TV | `braviatv` | 3 min | Lokaal netwerk |
| Samsung TV | `samsungtv` | 3 min | Lokaal netwerk |
| LG webOS TV | `webostv` | 3 min | Lokaal netwerk |
| Android TV / Google TV | `androidtv` | 3 min | Lokaal netwerk |
| Apple TV | `apple_tv` | 3 min | Lokaal netwerk |
| Roku | `roku` | 3 min | Lokaal netwerk |
| Yamaha MusicCast | `yamaha_musiccast` | 3 min | Lokaal netwerk |
| Denon / Marantz AVR | `denon` | 3 min | Lokaal netwerk |
| Onkyo / Pioneer AVR | `onkyo` | 3 min | Lokaal netwerk |
| Logitech Harmony | `harmony` | 5 min | Hub vereist |
| Netatmo | `netatmo` | 10 min | Cloudpolling, hoge latentie |
| Tado | `tado` | 10 min | Cloudpolling |
| Daikin | `daikin` | 5 min | Lokaal + cloud gemengd |
| ecobee | `ecobee` | 10 min | Cloudpolling |
| Google Nest | `nest` | 10 min | Cloudpolling |
| HomeWizard Energy | `homewizard` | 3 min | Lokaal LAN |
| Tibber | `tibber` | 10 min | Cloud-API |
| SMA Solar | `sma` | 10 min | Cloud / lokale Modbus |
| SolarEdge | `solaredge` | 10 min | Cloudpolling |
| Fronius | `fronius` | 10 min | Cloudpolling |
| Tesla Powerwall | `powerwall` | 5 min | Meestal lokaal |
| Nuki Smart Lock | `nuki` | 5 min | BLE-bridge / cloud |
| August Smart Lock | `august` | 5 min | Cloud |
| Yale Smart Alarm | `yale_smart_alarm` | 5 min | Cloud |
| Ring | `ring` | 10 min | Cloudcamera |
| Blink | `blink` | 10 min | Cloudcamera |
| Arlo | `arlo` | 10 min | Cloudcamera |
| DoorBird | `doorbird` | 3 min | Lokaal LAN |
| Reolink | `reolink` | 3 min | Lokaal LAN |
| Amcrest | `amcrest` | 3 min | Lokaal LAN |
| Eufy Security | `eufy_security` | 5 min | Cloud |
| SimpliSafe | `simplisafe` | 10 min | Cloud |
| Abode | `abode` | 10 min | Cloud |
| UniFi (Ubiquiti) | `unifi` | 3 min | Lokaal LAN |
| AVM FRITZ!Box | `fritz` | 5 min | Lokaal LAN |
| MikroTik | `mikrotik` | 3 min | Lokaal LAN |
| ASUS Router | `asusrouter` | 3 min | Lokaal LAN |
| Synology NAS | `synology_dsm` | 3 min | Lokaal LAN |
| Viessmann ViCare | `vicare` | 10 min | Cloud |
| Vaillant (myVaillant) | `vaillant` | 10 min | Cloud |
| Bosch Smart Home | `bosch_shc` | 5 min | Lokale controller |
| Mitsubishi MelCloud | `melcloud` | 10 min | Cloud |
| NIBE heat pump | `nibe_heatpump` | 10 min | Cloud / lokaal |
| Huawei Solar | `huawei_solar` | 5 min | Lokale Modbus |
| Enphase Envoy | `enphase_envoy` | 5 min | Lokaal LAN |
| GoodWe | `goodwe` | 10 min | Cloud |
| Growatt | `growatt_server` | 10 min | Cloud |
| EcoFlow | `ecoflow` | 10 min | Cloud |
| Roborock | `roborock` | 3 min | Lokaal + cloud |
| ECOVACS | `ecovacs` | 5 min | Cloud |
| Neato Robotics | `neato` | 5 min | Cloud |
| LG ThinQ | `lg_thinq` | 5 min | Cloud |
| Meross | `meross` | 3 min | Lokaal + cloud |
| Belkin WeMo | `wemo` | 3 min | Lokaal LAN |
| myQ (Chamberlain / LiftMaster) | `myq` | 5 min | Cloud |
| Nice G.O. | `nice_go` | 5 min | Cloud |
| Ecowitt | `ecowitt` | 10 min | Lokaal, zelden kritiek |
| Ambient Weather Station | `ambient_station` | 10 min | Cloud / lokaal |
| Husqvarna Automower | `husqvarna_automower` | 10 min | Cloud |
| GARDENA Bluetooth | `gardena_bluetooth` | 20 min | Passieve BLE |
| MQTT | `mqtt` | 5 min | Aanpassen per apparaat – sterk variabel |
| HomeKit Controller | `homekit_controller` | 5 min | Lokaal HomeKit |
| Lutron Caséta | `lutron_caseta` | 3 min | Lokale bridge |
| SwitchBot | `switchbot` | 10 min | BLE / cloud |
| iRobot Roomba | `roomba` | 5 min | Cloud |

> ⚠️ **Voor ontwikkelaars:** Wanneer een nieuw protocol wordt toegevoegd aan `KNOWN_PROTOCOLS` in `const.py`, **moet** een bijbehorende aanbevolen vertraging worden toegevoegd aan `PROTOCOL_DELAY_HINTS` in hetzelfde bestand, en moet een nieuwe rij worden toegevoegd aan deze tabel in alle vijf taalbestanden.

---

### Watch label – aangepaste offline-indicatoren

Met de **watch label**-functie kun je *elk* apparaat bewaken dat Connection Observer niet via het standaard `unavailable`-pad kan bewaken — bijvoorbeeld:

- **Passieve BLE-sensoren** (BTHome, GARDENA Bluetooth): geen persistente verbinding, HA stelt pas na uren `unavailable` in
- **Cloudapparaten** die "beschikbaar" blijven ook al is het fysieke apparaat defect of onbereikbaar
- **Elk aangepast scenario** waarbij je een binaire sensor kunt maken die de werkelijke verbindingsstatus weergeeft

#### Hoe het werkt

1. Maak een **template binaire sensor** (of een andere binaire entiteit) die `on` wordt wanneer je apparaat offline is en `off` wanneer het online is.
2. Maak in de HA-labeleditor (**Instellingen → Labels**) een label aan met de exacte naam die je in de Expert-stap hebt geconfigureerd (bijv. `offline_indicator`).
3. Wijs dat label toe aan je template binaire sensor.
4. Connection Observer neemt automatisch alle entiteiten met dit label op en bewaakt hun status:
   - `on` → maakt een offline-gebeurtenis aan (protocol weergegeven als `custom`)
   - `off` → markeert het apparaat als weer online

#### Voorbeeld: versheidsmonitor voor BTHome deursensor

Maak een template binaire sensor die controleert of de laatste update meer dan 2 uur geleden was:

```yaml
# configuration.yaml
template:
  - binary_sensor:
      - name: "BTHome Deur Offline Indicator"
        unique_id: bthome_deur_offline_indicator
        state: >
          {{ (now() - states.sensor.bthome_deur_contact.last_updated).total_seconds() > 7200 }}
        device_class: problem
```

Vervolgens:
1. Ga naar **Instellingen → Labels** → maak een label aan met de naam `offline_indicator`
2. Ga naar **Instellingen → Apparaten en diensten → Entiteiten** → zoek `binary_sensor.bthome_deur_offline_indicator` → wijs het label `offline_indicator` toe
3. Stel in de Expert-stap van Connection Observer **Watch label** in op `offline_indicator`

Connection Observer maakt nu een offline-gebeurtenis aan wanneer de BTHome-sensor meer dan 2 uur niets heeft gerapporteerd, en sluit deze automatisch bij een nieuw rapport.

> **Tip:** Je kunt meerdere entiteiten labelen met hetzelfde watch label. Elke entiteit wordt onafhankelijk bewaakt. De apparaatnaam in meldingen is de weergavenaam van de gelabelde entiteit.

---

### Aanbevolen beginconfiguratie

- **Directe melding:** uit
- **Samenvatting:** aan, dagelijks om 08:00
- **Vertraging:** 5 minuten globaal (vermijdt valse alarmen door korte WiFi-uitval)
- **Vertraging per protocol:** gebruik "Aanbevolen vertragingen toepassen" voor een snelle instelling
- **Minimale offline-duur:** 5 minuten (houdt de samenvatting overzichtelijk)
- **Zone opnemen:** aan (maakt meldingen veel leesbaarder)
- **HA Repairs drempelwaarde:** 24 uur
- **Watch label:** stel in voor passieve BLE- of aangepaste apparaten die je wilt bewaken

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

### Groepsmelding bij gelijktijdige uitval (≥ 5 apparaten)

Wanneer 5 of meer apparaten binnen 5 seconden offline gaan, wordt één groepsmelding verzonden in plaats van afzonderlijke meldingen. Dit voorkomt een stortvloed van meldingen bij een router-herstart of een korte infrastructuurstoring.

**Verbindingsuitval:**
> **Verbindingsuitval – 8 apparaten**
> ⚠️ 8 apparaten tegelijk offline — waarschijnlijk een infrastructuurprobleem (bijv. router herstart).
> • Woonkamer Stekker (shelly)
> • Keuken Sensor (zha)
> • Gang Lamp (hue)
> • Slaapkamer Lamp (hue)
> • Kantoor Schakelaar (esphome)
> • …

**Herverbinding:**
> **Verbinding hersteld – 8 apparaten**
> ✅ 8 apparaten weer online:
> • Woonkamer Stekker
> • Keuken Sensor
> • Gang Lamp
> • Slaapkamer Lamp
> • Kantoor Schakelaar
> • …

Als minder dan 5 apparaten zijn getroffen, worden individuele meldingen verzonden zoals gebruikelijk (inclusief cooldown-controle).

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

Voeg het toe aan de lijst *Uitgesloten apparaten* in de geavanceerde instellingen. Alle entiteiten van dat apparaat worden dan genegeerd. Als het apparaat op het moment van opslaan offline is, wordt het direct uit de offline-lijst verwijderd en een openstaand HA Repairs-probleem automatisch opgelost.

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
- **Passieve BLE-apparaten (BTHome etc.):** Bluetooth Low Energy-sensoren zoals BTHome deur-/raamsensoren onderhouden geen persistente verbinding — ze zenden periodieke berichten uit. Als zo'n apparaat offline gaat (bijv. batterij verwijderd), stelt Home Assistant de entiteiten pas op `unavailable` na een eigen interne time-out, die enkele uren kan bedragen. Connection Observer kan pas reageren zodra HA `unavailable` meldt. Realtime bewaking is voor passieve BLE-apparaten structureel niet mogelijk, in tegenstelling tot WiFi-apparaten. **Oplossing vanaf v1.1.0:** Gebruik de [Watch label](#watch-label--aangepaste-offline-indicatoren)-functie met een template binaire sensor die `last_updated` bewaakt — dit maakt detectie binnen enkele minuten mogelijk.
- **Zigbee2MQTT – beschikbaarheidscontrole vereist:** Connection Observer reageert op de `unavailable`-status van entiteiten. Zigbee2MQTT stelt deze status standaard **niet** in — beschikbaarheidscontroles moeten worden ingeschakeld in Z2M: **Instellingen → Beschikbaarheid → ingeschakeld**. Zonder deze instelling worden Z2M-apparaten niet gedetecteerd.
- **Slechts één instantie:** Connection Observer ondersteunt één integratie-instantie per HA-installatie.
- **30 dagen bewaring:** Gebeurtenissen ouder dan 30 dagen worden automatisch verwijderd.
