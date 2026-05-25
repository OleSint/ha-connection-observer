# Connection Observer – Documentation (Français)

**Version:** 1.0.4  
**Dépôt :** [github.com/OleSint/ha-connection-observer](https://github.com/OleSint/ha-connection-observer)

---

## Table des matières

1. [Qu'est-ce que Connection Observer ?](#1-quest-ce-que-connection-observer-)
2. [Fonctionnement](#2-fonctionnement)
3. [Installation](#3-installation)
4. [Assistant de configuration](#4-assistant-de-configuration)
5. [Options de configuration](#5-options-de-configuration)
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

L'assistant de configuration vous guide à travers quatre étapes. Tous les paramètres peuvent être modifiés ensuite via le bouton **Configurer** de la carte d'intégration.

### Étape 1 – Protocoles

**Ce que vous sélectionnez ici détermine quels appareils sont surveillés.**

L'assistant n'affiche que les familles d'intégration réellement configurées dans votre instance HA.

| Champ | Description |
|---|---|
| **Protocoles à surveiller** | Sélection multiple. Choisissez une ou plusieurs familles d'intégration. |
| **Langue des notifications** | Choisissez English, Deutsch, Français, Nederlands ou Español. |

> **Conseil :** Vous pouvez toujours ajouter ou supprimer des protocoles ultérieurement. Les nouveaux appareils d'un protocole sélectionné sont automatiquement pris en charge.

> **Utilisateurs de Zigbee2MQTT :** Les appareils Zigbee2MQTT apparaissent dans HA sous le domaine d'intégration `mqtt` — il n'existe pas d'entrée Zigbee2MQTT séparée. Sélectionnez **MQTT** pour les surveiller. Notez que cela inclura également tous les autres appareils MQTT de votre installation (p. ex. Tasmota, capteurs personnalisés). Un filtrage par étiquettes (labels) est prévu pour une version future afin de permettre un contrôle plus précis.

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

| Champ | Description |
|---|---|
| **Délai d'alerte** | Minutes hors ligne avant la création d'un événement. Par défaut : **0** (immédiat). |
| **Délai entre notifications** | Temps minimum entre les notifications immédiates pour le même appareil. Par défaut : **0** (pas de limite). |
| **Durée minimale hors ligne** | Événements plus courts exclus du résumé. Par défaut : **0** (tous les événements). |
| **Inclure la pièce / zone** | Afficher le nom de la zone HA dans les notifications. Par défaut : **désactivé**. |
| **Inclure fabricant & modèle** | Afficher les informations de l'appareil. Par défaut : **désactivé**. |
| **Domaines d'entités exclus** | Exclure des domaines d'entités entiers de la surveillance (ex. `sensor`, `button`). Les entités `device_tracker` sont toujours exclues automatiquement. |
| **Entités exclues** | Liste d'entités spécifiques à exclure de la surveillance. |

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

### Configuration de départ recommandée

- **Notification immédiate :** désactivée
- **Résumé :** activé, quotidien à 08h00
- **Délai d'alerte :** 5 minutes (évite les fausses alarmes dues aux coupures WiFi brèves)
- **Durée minimale hors ligne :** 5 minutes (garde le résumé lisible)
- **Inclure la zone :** activé (rend les notifications bien plus lisibles)
- **Seuil HA Repairs :** 24 heures

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

Ajoutez-la à la liste *Entités exclues* dans les paramètres avancés. Les autres entités de l'appareil restent surveillées.

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
- **Appareils BLE passifs (BTHome etc.) :** Les capteurs Bluetooth Low Energy comme les capteurs de porte/fenêtre BTHome ne maintiennent pas de connexion persistante — ils diffusent des annonces périodiques. Si un tel appareil passe hors ligne (p. ex. batterie retirée), Home Assistant ne met ses entités à `unavailable` qu'après son propre délai interne, qui peut atteindre plusieurs heures. Connection Observer ne peut réagir qu'une fois que HA signale `unavailable`. La surveillance en temps réel n'est donc structurellement pas possible pour les appareils BLE passifs, contrairement aux appareils WiFi.
- **Une seule instance :** Connection Observer supporte une seule instance par installation HA.
- **Conservation des événements 30 jours :** Les événements de plus de 30 jours sont automatiquement supprimés.
