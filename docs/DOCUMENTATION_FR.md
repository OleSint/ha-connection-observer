# Connection Observer – Documentation (Français)

**Version:** 1.2.0  
**Dépôt :** [github.com/OleSint/ha-connection-observer](https://github.com/OleSint/ha-connection-observer)

---

## Table des matières

1. [Qu'est-ce que Connection Observer ?](#1-quest-ce-que-connection-observer-)
2. [Fonctionnement](#2-fonctionnement)
3. [Installation](#3-installation)
4. [Assistant de configuration](#4-assistant-de-configuration)
5. [Options de configuration](#5-options-de-configuration)
   - [Délais d'alerte par protocole](#délais-dalerte-par-protocole)
   - [Watch label – indicateurs hors ligne personnalisés](#watch-label--indicateurs-hors-ligne-personnalisés)
6. [Modèles de notification](#6-modèles-de-notification)
7. [Intégration HA Repairs](#7-intégration-ha-repairs)
8. [Entités](#8-entités)
9. [Services](#9-services)
10. [Formats de notification](#10-formats-de-notification)
11. [Cas d'utilisation avancés](#11-cas-dutilisation-avancés)
12. [Dépannage](#12-dépannage)
13. [Limitations connues](#13-limitations-connues)

---

## 1. Qu'est-ce que Connection Observer ?

Connection Observer est une intégration personnalisée pour Home Assistant qui surveille en permanence la connectivité de vos appareils domotiques et vous alerte lorsque quelque chose passe hors ligne — avant même que vous ne remarquiez qu'un interrupteur ne répond plus ou qu'un capteur n'envoie plus de données.

**L'idée centrale** est de surveiller par *famille de protocoles* plutôt que par entité individuelle. Au lieu de sélectionner 200 entités une par une, vous choisissez simplement « surveiller tous les appareils Zigbee » ou « surveiller tous les appareils ESPHome ». Chaque appareil appartenant à cette famille d'intégration est automatiquement couvert — y compris les nouveaux appareils que vous ajouterez plus tard.

---

## 2. Fonctionnement

### L'état `unavailable`

Home Assistant dispose d'un mécanisme intégré pour signaler qu'un appareil n'est plus joignable : il met toutes les entités de cet appareil à l'état `unavailable`. Cela se produit automatiquement lorsque :

- Un appareil Zigbee ou Z-Wave ne répond plus au coordinateur
- Un appareil WiFi (ESPHome, Shelly, etc.) n'est plus accessible sur le réseau
- Une ampoule Hue est éteinte au mur et le pont perd le contact
- Toute autre intégration détecte que la communication est interrompue

Connection Observer écoute exactement cette transition : de n'importe quel état → `unavailable`. Lorsqu'il la détecte, il crée un *événement de déconnexion* pour l'appareil concerné.

### Déduplication au niveau de l'appareil

La plupart des appareils exposent plusieurs entités dans Home Assistant. Une prise Zigbee peut avoir des entités pour l'état de l'interrupteur, la puissance actuelle, l'énergie totale, la tension, etc. Lorsque cette prise passe hors ligne, toutes les entités deviennent `unavailable` en même temps.

Connection Observer détermine à quel *appareil* appartient une entité via le registre des appareils HA, et ne crée qu'**un seul événement par appareil** — quel que soit le nombre d'entités. Cela signifie une notification par appareil, pas cinq.

### Protection au démarrage

Lorsque Home Assistant redémarre, toutes les intégrations ont besoin d'un moment pour reconnecter leurs appareils. Durant cette fenêtre, de nombreuses entités passent brièvement par `unavailable`. Connection Observer attend 60 secondes après le démarrage complet de HA avant de commencer le suivi des déconnexions. Cela évite un déluge de fausses alarmes à chaque redémarrage de HA.

### Stockage persistant

Tous les événements de déconnexion sont enregistrés dans le système de stockage intégré de HA (`~/.homeassistant/.storage/`). Les événements survivent aux redémarrages de HA et sont conservés jusqu'à 30 jours.

### Chien de garde (Watchdog)

Toutes les 5 minutes, Connection Observer vérifie activement si les appareils ayant des événements ouverts (c'est-à-dire sans reconnexion enregistrée) sont réellement encore indisponibles. Si un appareil est revenu en ligne sans produire d'événement `state_changed`, le watchdog le détecte et ferme l'événement.

---

## 3. Installation

### Via HACS (recommandé)

1. Assurez-vous que HACS est installé dans votre instance Home Assistant. Sinon, suivez le [guide d'installation HACS](https://hacs.xyz/docs/setup/download).
2. Ouvrez **HACS → Intégrations** dans la barre latérale HA.
3. Cliquez sur le **menu à trois points** (en haut à droite) → **Dépôts personnalisés**.
4. Entrez `https://github.com/OleSint/ha-connection-observer` comme URL et sélectionnez **Intégration** comme catégorie. Cliquez sur **Ajouter**.
5. Recherchez **Connection Observer** dans la liste HACS et cliquez sur **Télécharger**.
6. **Redémarrez Home Assistant.**
7. Après le redémarrage, allez dans **Paramètres → Appareils et services → Ajouter une intégration** et recherchez **Connection Observer**.

### Installation manuelle

1. Téléchargez la dernière version depuis la [page des releases GitHub](https://github.com/OleSint/ha-connection-observer/releases).
2. Extrayez l'archive et copiez le dossier `custom_components/connection_observer` dans votre répertoire de configuration HA sous `config/custom_components/connection_observer`.
3. **Redémarrez Home Assistant.**
4. Après le redémarrage, allez dans **Paramètres → Appareils et services → Ajouter une intégration** et recherchez **Connection Observer**.

---

## 4. Assistant de configuration

L'assistant de configuration vous guide à travers cinq étapes. Tous les paramètres peuvent être modifiés ensuite via le bouton **Configurer** de la carte d'intégration.

### Étape 1 – Protocoles

**Ce que vous sélectionnez ici détermine quels appareils sont surveillés.**

L'assistant n'affiche que les familles d'intégration réellement configurées dans votre instance HA.

| Champ | Description |
|---|---|
| **Protocoles à surveiller** | Sélection multiple. Choisissez une ou plusieurs familles d'intégration. |
| **Langue des notifications** | Choisissez English, Deutsch, Français, Nederlands ou Español. |

> **Conseil :** Vous pouvez toujours ajouter ou supprimer des protocoles ultérieurement. Les nouveaux appareils d'un protocole sélectionné sont automatiquement pris en charge.

> **Utilisateurs de Zigbee2MQTT :** Les appareils Zigbee2MQTT apparaissent dans HA sous le domaine d'intégration `mqtt` — il n'existe pas d'entrée Zigbee2MQTT séparée. Sélectionnez **MQTT** pour les surveiller. Notez que cela inclura également tous les autres appareils MQTT de votre installation (p. ex. Tasmota, capteurs personnalisés). Un filtrage par étiquettes (labels) est prévu pour une version future afin de permettre un contrôle plus précis.

> ⚠️ **Important :** Connection Observer ne peut détecter les appareils que lorsque HA les passe à `unavailable`. Zigbee2MQTT ne le fait **pas** par défaut — vous devez d'abord activer les contrôles de disponibilité : **Zigbee2MQTT → Paramètres → Disponibilité → activé**. Sans ce paramètre, Connection Observer ne peut pas détecter les appareils Z2M hors ligne.

### Étape 2 – Notifications

**Configurez comment et quand recevoir des alertes.**

| Champ | Description |
|---|---|
| **Service(s) de notification** | Sélection multiple. Choisissez un ou plusieurs services `notify.*`. |
| **Notification immédiate** | Si activé, une notification est envoyée dès qu'un appareil passe hors ligne. Par défaut : **désactivé**. |
| **Résumé planifié** | Si activé, un résumé est envoyé à l'heure configurée. Par défaut : **activé**. |
| **Heure du résumé** | Heure de la journée pour le résumé. |
| **Jours du résumé** | Jours de la semaine pour le résumé. Par défaut : tous les jours. |
| **Notifier à la reconnexion** | Opt-in. Notification lorsqu'un appareil revient en ligne. Par défaut : **désactivé**. |

### Étape 3 – Test

Une étape de test optionnelle envoie une notification à tous vos services sélectionnés pour vérifier que tout fonctionne correctement.

- Cochez **Envoyer une notification de test maintenant** (précoché) et cliquez sur Soumettre.
- Décochez la case pour ignorer cette étape.
- En cas d'échec, une erreur s'affiche. Vous pouvez réessayer ou décocher la case pour continuer quand même.

### Étape 4 – Avancé

**Tous les champs sont facultatifs. La valeur 0 désactive la fonctionnalité correspondante.**  
Le **délai d'alerte global** défini ici s'applique à tous les protocoles, sauf si un délai spécifique est défini à l'étape 5.

| Champ | Description |
|---|---|
| **Délai d'alerte** | Minutes hors ligne avant la création d'un événement. Par défaut : **0** (immédiat). |
| **Délai entre notifications** | Temps minimum entre les notifications immédiates pour le même appareil. Par défaut : **0** (pas de limite). |
| **Durée minimale hors ligne** | Événements plus courts exclus du résumé. Par défaut : **0** (tous les événements). |
| **Inclure la pièce / zone** | Afficher le nom de la zone HA dans les notifications. Par défaut : **désactivé**. |
| **Inclure fabricant & modèle** | Afficher les informations de l'appareil. Par défaut : **désactivé**. |
| **Domaines d'entités exclus** | Exclure des domaines d'entités entiers de la surveillance (ex. `sensor`, `button`). Les entités `device_tracker` sont toujours exclues automatiquement. |
| **Appareils exclus** | Liste d'appareils spécifiques à exclure entièrement de la surveillance. Seuls les appareils disposant d'au moins une entité sur un protocole configuré sont affichés — les services virtuels (HACS, Superviseur, Add-ons, etc.) n'apparaissent pas. Si un appareil est ajouté alors qu'il est hors ligne, il est immédiatement retiré de la liste hors ligne et tout problème HA Repairs ouvert est résolu. |

### Étape 5 – Expert

**Les deux fonctions sont facultatives. Ignorez cette étape si vous n'avez besoin que du délai global.**

#### Délais d'alerte par protocole

Chaque protocole sélectionné à l'étape 1 apparaît ici avec son propre champ de délai. Une valeur **0** signifie « utiliser le délai d'alerte global de l'étape 4 ». Saisissez une valeur positive pour remplacer le délai global pour ce protocole spécifique.

**Conseil : Appliquer les délais recommandés**  
Cochez la case **Appliquer les délais recommandés pour tous les protocoles** et cliquez sur Soumettre. Tous les champs de délai sont pré-remplis avec les valeurs recommandées pour chaque protocole. Vous pouvez ensuite ajuster les valeurs individuelles ou les accepter telles quelles.

Les valeurs recommandées sont basées sur les caractéristiques de connexion typiques de chaque famille de protocoles :
- Protocoles TCP directs (ESPHome, Shelly, Tasmota) → **2 min** (connexion persistante, détection rapide)
- Protocoles maillés locaux (ZHA, Z-Wave JS) → **5 min** (le ré-acheminement maillé prend un moment)
- BLE passif (BTHome, GARDENA Bluetooth) → **20 min** (cycles d'annonce rares)
- Protocoles cloud (Tuya, Nest, Ring…) → **10 min** (latence de sondage)

Voir le [tableau de référence complet](#délais-dalerte-par-protocole) dans la Section 5 pour toutes les valeurs.

#### Watch label – indicateurs hors ligne personnalisés

Saisissez ici le nom d'un label HA (p. ex. `indicateur_hors_ligne`). Toute entité à laquelle vous assignez ce label dans l'éditeur de labels de Home Assistant sera traitée comme un indicateur hors ligne personnalisé par Connection Observer :

- Lorsque l'état de l'entité passe à **`on`** → Connection Observer crée un événement hors ligne (protocole affiché : `custom`)
- Lorsque l'état de l'entité passe à **`off`** → Connection Observer marque l'appareil comme de nouveau en ligne

Cette fonction est volontairement générique : étiquetez n'importe quelle entité — un capteur binaire template, un helper ou toute entité binaire — et Connection Observer réagira à ses changements d'état.

**Cas d'utilisation typique :** les appareils BLE passifs (capteurs BTHome, GARDENA Bluetooth) ne peuvent pas être surveillés en temps réel via l'état `unavailable`. Voir les [Limitations connues](#13-limitations-connues) et le [Watch label](#watch-label--indicateurs-hors-ligne-personnalisés) dans la Section 5 pour un exemple complet étape par étape.

---

## 5. Options de configuration

Tous les paramètres de l'assistant peuvent être modifiés à tout moment via **Paramètres → Appareils et services → Connection Observer → Configurer**.

En plus des paramètres de l'assistant, la page d'options propose également :

### Notification de test

Après avoir enregistré vos paramètres, une étape de test apparaît. Cochez **Envoyer une notification de test maintenant** et cliquez sur Soumettre pour envoyer un test en direct. Utile après chaque changement de service de notification.

### Exclusions de domaines

Des domaines d'entités entiers peuvent être exclus sur la page d'options. Les entités `device_tracker` sont toujours exclues automatiquement.

### Seuil HA Repairs

Définit le nombre d'heures qu'un appareil doit être hors ligne avant qu'un problème persistant soit créé dans **Paramètres → Réparations**. La valeur `0` désactive cette fonction. Par défaut : **24 heures**.

Voir la [Section 7](#7-intégration-ha-repairs) pour plus de détails.

### Modèles de notification

Sept champs de texte optionnels permettent de personnaliser le format de n'importe quelle notification. Laissez un champ vide pour utiliser le texte par défaut selon la langue.

Voir la [Section 6](#6-modèles-de-notification) pour plus de détails.

### Délais d'alerte par protocole

Chaque protocole sélectionné peut avoir son propre délai d'alerte qui remplace la valeur globale. Définissez le délai d'un protocole à **0** (ou laissez-le absent) pour utiliser le délai global.

**Configuration en un clic :** Dans l'étape Expert (assistant) ou la page Expert (options), cochez **Appliquer les délais recommandés** et cliquez sur Soumettre. Tous les champs sont pré-remplis automatiquement.

| Protocole | Domaine | Délai recommandé | Raison |
|---|---|---:|---|
| Zigbee (ZHA) | `zha` | 5 min | Le routage maillé prend un moment |
| Zigbee (deCONZ) | `deconz` | 5 min | Le routage maillé prend un moment |
| Z-Wave (Z-Wave JS) | `zwave_js` | 5 min | Le routage maillé prend un moment |
| Matter | `matter` | 5 min | Comportement similaire au maillage |
| Thread (OTBR) | `otbr` | 5 min | Maillage Thread |
| Bluetooth | `bluetooth` | 10 min | La connexion BLE est plus lente |
| BTHome | `bthome` | 20 min | BLE passif – annonces rares |
| RFXtrx (433 MHz) | `rfxtrx` | 10 min | RF unidirectionnel, sans accusé de réception |
| MySensors | `mysensors` | 10 min | Sondage lent |
| Insteon | `insteon` | 5 min | Bus propriétaire, sondage |
| KNX | `knx` | 5 min | Bus filaire, fiable mais sondé |
| Velbus | `velbus` | 5 min | Bus filaire |
| ESPHome | `esphome` | 2 min | TCP persistant, détection très rapide |
| Shelly | `shelly` | 2 min | TCP persistant, détection très rapide |
| Tasmota | `tasmota` | 2 min | TCP persistant, détection très rapide |
| Tuya | `tuya` | 5 min | Sondage cloud |
| WLED | `wled` | 2 min | TCP local |
| TP-Link (Kasa/Tapo) | `tplink` | 3 min | TCP local |
| TP-Link Omada | `tplink_omada` | 3 min | TCP local |
| Broadlink | `broadlink` | 3 min | TCP local |
| Philips Hue | `hue` | 3 min | Pont Hue local |
| IKEA TRÅDFRI | `tradfri` | 5 min | Le hub IKEA peut être lent |
| LIFX | `lifx` | 3 min | UDP/TCP local |
| Nanoleaf | `nanoleaf` | 3 min | TCP local |
| Yeelight | `yeelight` | 2 min | TCP local |
| Xiaomi Mi Home | `xiaomi_miio` | 5 min | Mixte local + cloud |
| Sonos | `sonos` | 3 min | Réseau local |
| Google Cast | `cast` | 3 min | Réseau local |
| Logitech Media Server | `squeezebox` | 5 min | Dépend du serveur |
| Kodi | `kodi` | 3 min | Réseau local |
| Plex | `plex` | 5 min | Dépend du serveur |
| Sony Bravia TV | `braviatv` | 3 min | Réseau local |
| Samsung TV | `samsungtv` | 3 min | Réseau local |
| LG webOS TV | `webostv` | 3 min | Réseau local |
| Android TV / Google TV | `androidtv` | 3 min | Réseau local |
| Apple TV | `apple_tv` | 3 min | Réseau local |
| Roku | `roku` | 3 min | Réseau local |
| Yamaha MusicCast | `yamaha_musiccast` | 3 min | Réseau local |
| Denon / Marantz AVR | `denon` | 3 min | Réseau local |
| Onkyo / Pioneer AVR | `onkyo` | 3 min | Réseau local |
| Logitech Harmony | `harmony` | 5 min | Hub requis |
| Netatmo | `netatmo` | 10 min | Sondage cloud, latence élevée |
| Tado | `tado` | 10 min | Sondage cloud |
| Daikin | `daikin` | 5 min | Mixte local + cloud |
| ecobee | `ecobee` | 10 min | Sondage cloud |
| Google Nest | `nest` | 10 min | Sondage cloud |
| HomeWizard Energy | `homewizard` | 3 min | LAN local |
| Tibber | `tibber` | 10 min | API cloud |
| SMA Solar | `sma` | 10 min | Cloud / Modbus local |
| SolarEdge | `solaredge` | 10 min | Sondage cloud |
| Fronius | `fronius` | 10 min | Sondage cloud |
| Tesla Powerwall | `powerwall` | 5 min | Généralement local |
| Nuki Smart Lock | `nuki` | 5 min | Pont BLE / cloud |
| August Smart Lock | `august` | 5 min | Cloud |
| Yale Smart Alarm | `yale_smart_alarm` | 5 min | Cloud |
| Ring | `ring` | 10 min | Caméra cloud |
| Blink | `blink` | 10 min | Caméra cloud |
| Arlo | `arlo` | 10 min | Caméra cloud |
| DoorBird | `doorbird` | 3 min | LAN local |
| Reolink | `reolink` | 3 min | LAN local |
| Amcrest | `amcrest` | 3 min | LAN local |
| Eufy Security | `eufy_security` | 5 min | Cloud |
| SimpliSafe | `simplisafe` | 10 min | Cloud |
| Abode | `abode` | 10 min | Cloud |
| UniFi (Ubiquiti) | `unifi` | 3 min | LAN local |
| AVM FRITZ!Box | `fritz` | 5 min | LAN local |
| MikroTik | `mikrotik` | 3 min | LAN local |
| ASUS Router | `asusrouter` | 3 min | LAN local |
| Synology NAS | `synology_dsm` | 3 min | LAN local |
| Viessmann ViCare | `vicare` | 10 min | Cloud |
| Vaillant (myVaillant) | `vaillant` | 10 min | Cloud |
| Bosch Smart Home | `bosch_shc` | 5 min | Contrôleur local |
| Mitsubishi MelCloud | `melcloud` | 10 min | Cloud |
| NIBE heat pump | `nibe_heatpump` | 10 min | Cloud / local |
| Huawei Solar | `huawei_solar` | 5 min | Modbus local |
| Enphase Envoy | `enphase_envoy` | 5 min | LAN local |
| GoodWe | `goodwe` | 10 min | Cloud |
| Growatt | `growatt_server` | 10 min | Cloud |
| EcoFlow | `ecoflow` | 10 min | Cloud |
| Roborock | `roborock` | 3 min | Local + cloud |
| ECOVACS | `ecovacs` | 5 min | Cloud |
| Neato Robotics | `neato` | 5 min | Cloud |
| LG ThinQ | `lg_thinq` | 5 min | Cloud |
| Meross | `meross` | 3 min | Local + cloud |
| Belkin WeMo | `wemo` | 3 min | LAN local |
| myQ (Chamberlain / LiftMaster) | `myq` | 5 min | Cloud |
| Nice G.O. | `nice_go` | 5 min | Cloud |
| Ecowitt | `ecowitt` | 10 min | Local, rarement critique |
| Ambient Weather Station | `ambient_station` | 10 min | Cloud / local |
| Husqvarna Automower | `husqvarna_automower` | 10 min | Cloud |
| GARDENA Bluetooth | `gardena_bluetooth` | 20 min | BLE passif |
| MQTT | `mqtt` | 5 min | À ajuster par appareil – très variable |
| HomeKit Controller | `homekit_controller` | 5 min | HomeKit local |
| Lutron Caséta | `lutron_caseta` | 3 min | Pont local |
| SwitchBot | `switchbot` | 10 min | BLE / cloud |
| iRobot Roomba | `roomba` | 5 min | Cloud |

> ⚠️ **Pour les développeurs :** Chaque fois qu'un nouveau protocole est ajouté à `KNOWN_PROTOCOLS` dans `const.py`, un délai recommandé correspondant **doit** être ajouté à `PROTOCOL_DELAY_HINTS` dans le même fichier, et une nouvelle ligne doit être ajoutée à ce tableau dans les cinq fichiers de documentation.

---

### Watch label – indicateurs hors ligne personnalisés

La fonction **watch label** vous permet de surveiller *n'importe quel* appareil que Connection Observer ne peut pas surveiller via le chemin `unavailable` standard — par exemple :

- **Capteurs BLE passifs** (BTHome, GARDENA Bluetooth) : pas de connexion persistante, HA ne passe à `unavailable` qu'au bout de plusieurs heures
- **Appareils cloud** qui restent « disponibles » même lorsque l'appareil physique est cassé ou injoignable
- **Tout scénario personnalisé** où vous pouvez créer un capteur binaire reflétant l'état de connexion réel

#### Fonctionnement

1. Créez un **capteur binaire template** (ou toute entité binaire) qui passe à `on` lorsque votre appareil est hors ligne et à `off` lorsqu'il est en ligne.
2. Dans l'éditeur de labels HA (**Paramètres → Labels**), créez un label avec le nom exact que vous avez configuré à l'étape Expert (p. ex. `indicateur_hors_ligne`).
3. Assignez ce label à votre capteur binaire template.
4. Connection Observer prend automatiquement en compte toutes les entités portant ce label et surveille leur état :
   - `on` → crée un événement hors ligne (protocole affiché : `custom`)
   - `off` → marque l'appareil comme de nouveau en ligne

#### Exemple : moniteur de fraîcheur pour capteur de porte BTHome

Créez un capteur binaire template qui vérifie si la dernière mise à jour remonte à plus de 2 heures :

```yaml
# configuration.yaml
template:
  - binary_sensor:
      - name: "BTHome Porte Indicateur Hors Ligne"
        unique_id: bthome_porte_indicateur_hors_ligne
        state: >
          {{ (now() - states.sensor.bthome_porte_contact.last_updated).total_seconds() > 7200 }}
        device_class: problem
```

Ensuite :
1. Allez dans **Paramètres → Labels** → créez un label nommé `indicateur_hors_ligne`
2. Allez dans **Paramètres → Appareils et services → Entités** → trouvez `binary_sensor.bthome_porte_indicateur_hors_ligne` → assignez le label `indicateur_hors_ligne`
3. Dans l'étape Expert de Connection Observer, définissez **Watch label** sur `indicateur_hors_ligne`

Connection Observer créera désormais un événement hors ligne chaque fois que le capteur BTHome n'a pas envoyé de rapport depuis plus de 2 heures, et le fermera automatiquement à l'arrivée d'un nouveau rapport.

> **Conseil :** Vous pouvez étiqueter plusieurs entités avec le même watch label. Chacune est surveillée indépendamment. Le nom d'appareil affiché dans les notifications est le nom convivial de l'entité étiquetée.

---

### Configuration de départ recommandée

- **Notification immédiate :** désactivée
- **Résumé :** activé, quotidien à 08h00
- **Délai d'alerte :** 5 minutes global (évite les fausses alarmes dues aux coupures WiFi brèves)
- **Délais par protocole :** utilisez « Appliquer les délais recommandés » pour une configuration rapide
- **Durée minimale hors ligne :** 5 minutes (garde le résumé lisible)
- **Inclure la zone :** activé (rend les notifications bien plus lisibles)
- **Seuil HA Repairs :** 24 heures
- **Watch label :** configurez-le pour les appareils BLE passifs ou personnalisés que vous souhaitez surveiller

---

## 6. Modèles de notification

Connection Observer envoie trois types de notifications : immédiat (déconnexion), reconnexion et résumé. Chaque type possède un titre et un corps de message personnalisables indépendamment.

### Modèles disponibles

Tous les champs de modèles se trouvent dans **Paramètres → Appareils et services → Connection Observer → Configurer**, en bas de la page d'options.

| Clé de modèle | S'applique à | Variables disponibles |
|---|---|---|
| `tmpl_imm_title` | Notification immédiate – titre | `{device_name}` `{protocol}` `{time}` `{area}` `{model}` |
| `tmpl_imm_msg` | Notification immédiate – corps | `{device_name}` `{protocol}` `{time}` `{area}` `{model}` |
| `tmpl_rec_title` | Reconnexion – titre | `{device_name}` |
| `tmpl_rec_msg` | Reconnexion – corps | `{device_name}` |
| `tmpl_sum_title` | Résumé – titre | `{count}` |
| `tmpl_sum_resolved` | Résumé – ligne pour événement résolu | `{device_name}` `{area}` `{protocol}` `{time_offline}` `{time_online}` |
| `tmpl_sum_ongoing` | Résumé – ligne pour appareil encore hors ligne | `{device_name}` `{area}` `{protocol}` `{time_offline}` |

### Notes sur les variables

- `{area}` est préformaté comme ` [Nom de la pièce]` (avec un espace initial) lorsque l'option *inclure la zone* est activée, ou comme chaîne vide sinon.
- `{model}` est `Fabricant – Modèle` ou vide.
- `{time}` / `{time_offline}` / `{time_online}` sont au format `HH:MM`. Pour `{time_offline}` dans le résumé, la date est incluse au format `MM/JJ HH:MM`.

### Notes importantes

- Si vous définissez un `tmpl_imm_msg` personnalisé, la deuxième ligne automatique avec la zone et le modèle (📍 …) n'est **pas** ajoutée. Incluez `{area}` et `{model}` dans votre modèle si vous souhaitez ces informations.
- Les erreurs de modèle (ex. faute de frappe dans un nom de variable) sont enregistrées comme avertissements.

---

## 7. Intégration HA Repairs

Lorsqu'un appareil est hors ligne depuis plus longtemps que le seuil configuré (par défaut : 24 heures), Connection Observer crée un problème persistant dans **Paramètres → Réparations**. Cela s'ajoute aux notifications habituelles.

### Ce que le problème affiche

L'entrée indique :
- Le nom de l'appareil
- Le protocole / l'intégration
- L'horodatage depuis lequel l'appareil est hors ligne

### Résolution automatique

Lorsque l'appareil revient en ligne — via un événement `state_changed` ou via le watchdog — le problème est **automatiquement supprimé**.

### Désactivation

Réglez **Signalement HA Repairs après N heures hors ligne** sur `0` dans les options.

---

## 8. Entités

Connection Observer crée trois entités par instance d'intégration.

### `sensor.connection_observer_offline_devices`

**Type :** Capteur | **Unité :** devices | **Icône :** `mdi:lan-disconnect`

Indique le nombre d'appareils actuellement hors ligne.

**Attributs d'état :**

| Attribut | Description |
|---|---|
| `devices` | Liste plate des noms d'appareils actuellement hors ligne. |
| `by_protocol` | Détail par protocole : nombre hors ligne et liste des appareils par famille d'intégration. |

L'attribut `by_protocol` a la structure suivante :

```yaml
by_protocol:
  shelly:
    offline: 1
    devices:
      - name: "Prise cuisine"
        offline_since: "22.05. 14:30"
        offline_duration: "2h 15m"
  bthome:
    offline: 0
    devices: []
```

Seuls les protocoles avec au moins un appareil hors ligne apparaissent dans cet attribut.

**Exemple — carte Markdown avec statut par protocole :**
```yaml
type: markdown
content: >
  {% set proto = state_attr('sensor.connection_observer_offline_devices', 'by_protocol') %}
  {% for p, data in proto.items() %}
  **{{ p }}**: {{ data.devices | map(attribute='name') | join(', ') }}
  (hors ligne depuis {{ data.devices[0].offline_since }})
  {% endfor %}
```

**Exemple dans une automatisation :**
```yaml
condition:
  - condition: numeric_state
    entity_id: sensor.connection_observer_offline_devices
    above: 0
```

---

### `sensor.connection_observer_pending_summary_events`

**Type :** Capteur | **Unité :** events | **Icône :** `mdi:clock-alert-outline`

Indique le nombre d'événements de déconnexion non encore inclus dans un résumé. Se remet à 0 après l'envoi d'un résumé ou après `clear_history`.

---

### `binary_sensor.connection_observer_connection_problem`

**Type :** Capteur binaire | **Classe :** `problem` | **Icône :** `mdi:check-network`

- **`ON`** – au moins un appareil est actuellement hors ligne
- **`OFF`** – tous les appareils surveillés sont joignables

**Exemple – alerte si le problème persiste plus de 10 minutes :**
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
      message: "Un appareil est hors ligne depuis plus de 10 minutes !"
```

---

## 9. Services

### `connection_observer.send_summary_now`

Envoie immédiatement un résumé de tous les événements en attente. Après l'appel, tous les événements en attente sont marqués comme inclus dans un résumé.

```yaml
service: connection_observer.send_summary_now
```

---

### `connection_observer.clear_history`

Efface tous les événements enregistrés de la mémoire et du stockage persistant. Supprime également toutes les entrées HA Repairs ouvertes.

> ⚠️ Cette action est irréversible.

```yaml
service: connection_observer.clear_history
```

---

### `connection_observer.clear_device`

Supprime tous les événements de déconnexion d'un **appareil spécifique** et résout toute entrée HA Repairs ouverte pour cet appareil. Les autres appareils ne sont pas affectés.

Passez n'importe quelle entité appartenant à l'appareil à effacer.

```yaml
service: connection_observer.clear_device
data:
  entity_id: light.salon_ampoule
```

---

## 10. Formats de notification

### Notification immédiate

**Basique :**
> **Connexion perdue**
> ⚠️ Prise Salon (shelly) a perdu la connexion à 14:32.

**Avec zone et informations d'appareil activées :**
> **Connexion perdue**
> ⚠️ Prise Salon (shelly) a perdu la connexion à 14:32.
> 📍 Salon  ·  Shelly Plus 1PM

### Notification de reconnexion (opt-in)

> **Connexion rétablie**
> ✅ Prise Salon est de nouveau en ligne.

### Notification groupée lors de pannes simultanées (≥ 5 appareils)

Lorsque 5 appareils ou plus se déconnectent en 5 secondes, une seule notification groupée est envoyée à la place des alertes individuelles. Cela évite une avalanche de notifications lors des redémarrages du routeur ou des brèves pannes d'infrastructure.

**Panne de connexion :**
> **Panne de connexion – 8 appareils**
> ⚠️ 8 appareils hors ligne simultanément — probable problème d'infrastructure (ex. redémarrage du routeur).
> • Prise Salon (shelly)
> • Capteur Cuisine (zha)
> • Lampe Couloir (hue)
> • Ampoule Chambre (hue)
> • Interrupteur Bureau (esphome)
> • …

**Reconnexion :**
> **Connexion rétablie – 8 appareils**
> ✅ 8 appareils de nouveau en ligne :
> • Prise Salon
> • Capteur Cuisine
> • Lampe Couloir
> • Ampoule Chambre
> • Interrupteur Bureau
> • …

Si moins de 5 appareils sont concernés, des notifications individuelles sont envoyées comme d'habitude (avec vérification du cooldown).

### Résumé

> **Résumé des connexions**
> 📋 3 appareil(s) affecté(s) depuis le dernier résumé :
> • Capteur Cuisine [Cuisine] (zha) : hors ligne depuis 05/19 07:15, de nouveau en ligne à 07:42
> • Ampoule Chambre [Chambre] (hue) : hors ligne depuis 05/19 09:05 ⚠️ toujours hors ligne
> • Détecteur Couloir (esphome) : hors ligne depuis 05/19 11:20, de nouveau en ligne à 11:28

---

## 11. Cas d'utilisation avancés

### Utiliser les modes immédiat et résumé simultanément

Activez les deux modes :
- **Délai d'alerte** de 3 à 5 minutes pour ignorer les coupures brèves
- **Notification immédiate** pour une prise de conscience en temps réel
- **Résumé** pour un aperçu quotidien
- **Durée minimale hors ligne** de 5 minutes pour n'afficher que les événements significatifs

### Combinaison avec des automatisations HA

```yaml
# Annoncer les appareils hors ligne via TTS s'ils sont encore offline à l'heure du coucher
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
        Attention : {{ states('sensor.connection_observer_offline_devices') }}
        appareil(s) sont actuellement hors ligne.
```

### Envoi vers plusieurs services

Sélectionnez plusieurs services dans le champ de service de notification. Tous reçoivent chaque notification simultanément.

### Exclure une entité spécifique

Ajoutez-le à la liste *Appareils exclus* dans les paramètres avancés. Toutes les entités de l'appareil seront ignorées. Si l'appareil est actuellement hors ligne au moment de la sauvegarde, il est immédiatement retiré de la liste hors ligne et tout problème HA Repairs ouvert est résolu automatiquement.

---

## 12. Dépannage

### Aucune notification n'est envoyée

1. Vérifiez qu'un service de notification est sélectionné dans **Configurer**.
2. Testez votre service notify directement via **Outils de développement → Services**.
3. Consultez le journal HA pour les erreurs `connection_observer`.
4. Assurez-vous que **Notification immédiate** ou **Résumé planifié** est activé.

### Le résumé n'est pas envoyé

1. Vérifiez que **Résumé planifié** est activé.
2. Vérifiez l'heure et les jours du résumé dans **Configurer**.
3. Vérifiez `sensor.connection_observer_pending_summary_events` — s'il est à 0, aucun événement n'est en attente.
4. Consultez le journal HA.

### Des appareils apparaissent hors ligne après un redémarrage de HA

Cela ne devrait pas se produire grâce à la période de grâce de 60 secondes. Si c'est le cas :
- L'appareil est peut-être réellement hors ligne.
- Si l'état dans HA n'est pas `unavailable`, le watchdog corrigera l'événement dans les 5 minutes.

### Un appareil apparaît hors ligne mais fonctionne correctement dans HA

Le watchdog s'exécute toutes les 5 minutes et fermera automatiquement l'événement. Vous pouvez aussi appeler `clear_history` pour réinitialiser immédiatement.

### L'entrée HA Repairs n'a pas été créée

1. Vérifiez que le seuil n'est pas à `0`.
2. L'appareil doit être hors ligne plus longtemps que le seuil. Le watchdog crée l'entrée lors de sa prochaine exécution (toutes les 5 minutes).

---

## 13. Limitations connues

- **Intégrations cloud uniquement :** Les appareils connectés exclusivement via un service cloud peuvent ne pas être détectés si l'intégration ne passe pas les entités à `unavailable`.
- **Intégrations par sondage :** Une déconnexion peut n'être détectée qu'après le prochain cycle de sondage.
- **Appareils BLE passifs (BTHome etc.) :** Les capteurs Bluetooth Low Energy comme les capteurs de porte/fenêtre BTHome ne maintiennent pas de connexion persistante — ils diffusent des annonces périodiques. Si un tel appareil passe hors ligne (p. ex. batterie retirée), Home Assistant ne met ses entités à `unavailable` qu'après son propre délai interne, qui peut atteindre plusieurs heures. Connection Observer ne peut réagir qu'une fois que HA signale `unavailable`. La surveillance en temps réel n'est donc structurellement pas possible pour les appareils BLE passifs, contrairement aux appareils WiFi. **Solution depuis la v1.1.0 :** Utilisez la fonction [Watch label](#watch-label--indicateurs-hors-ligne-personnalisés) avec un capteur binaire template qui surveille `last_updated` — cela permet une détection en quelques minutes.
- **Zigbee2MQTT – contrôle de disponibilité requis :** Connection Observer réagit à l'état `unavailable` des entités. Zigbee2MQTT ne définit **pas** cet état par défaut — les contrôles de disponibilité doivent être activés dans Z2M : **Paramètres → Disponibilité → activé**. Sans ce paramètre, les appareils Z2M ne seront pas détectés.
- **Une seule instance :** Connection Observer supporte une seule instance par installation HA.
- **Conservation des événements 30 jours :** Les événements de plus de 30 jours sont automatiquement supprimés.
