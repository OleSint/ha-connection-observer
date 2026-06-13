# Connection Observer – Documentation (English)

**Version:** 1.3.0  
**Repository:** [github.com/OleSint/ha-connection-observer](https://github.com/OleSint/ha-connection-observer)

---

## Table of Contents

1. [What is Connection Observer?](#1-what-is-connection-observer)
2. [How it works](#2-how-it-works)
3. [Installation](#3-installation)
4. [Setup wizard](#4-setup-wizard)
5. [Configuration options](#5-configuration-options)
   - [Observer labels](#observer-labels)
   - [Per-protocol alert delays](#per-protocol-alert-delays)
   - [Watch label – custom offline indicators](#watch-label--custom-offline-indicators)
6. [Notification templates](#6-notification-templates)
7. [HA Repairs integration](#7-ha-repairs-integration)
8. [Entities](#8-entities)
9. [Services](#9-services)
10. [Notification formats](#10-notification-formats)
11. [Advanced use cases](#11-advanced-use-cases)
12. [Troubleshooting](#12-troubleshooting)
13. [Known limitations](#13-known-limitations)

---

## 1. What is Connection Observer?

Connection Observer is a custom Home Assistant integration that continuously monitors the connectivity of your smart home devices and alerts you when something goes offline. Instead of noticing that a sensor has stopped reporting or a light switch no longer responds, you receive a notification the moment — or shortly after — a device loses its connection.

**The core idea** is to monitor by *protocol family* rather than by individual entity. Instead of selecting 200 individual entities, you simply choose "monitor all Zigbee devices" or "monitor all ESPHome devices". Every device belonging to that integration family is automatically covered — including new devices you add later.

---

## 2. How it works

### The `unavailable` state

Home Assistant has a built-in mechanism for signalling that a device can no longer be reached: it sets all entities belonging to that device to the state `unavailable`. This happens automatically when:

- A Zigbee or Z-Wave device stops responding to the coordinator
- A WiFi device (ESPHome, Shelly, etc.) is no longer reachable on the network
- A Hue bulb is switched off at the wall and the bridge loses contact
- Any other integration detects that communication has broken down

Connection Observer listens for exactly this transition: from any state → `unavailable`. When it detects this, it creates a *disconnect event* for the affected device.

### Device-level deduplication

Most devices expose multiple entities in Home Assistant. A Zigbee plug might have entities for the switch state, current power consumption, total energy, voltage, and more. When that plug goes offline, all five entities become `unavailable` at roughly the same time.

Connection Observer resolves which *device* an entity belongs to via the HA device registry, and only creates **one event per device** — regardless of how many entities it has. This means one notification per device, not five.

### Startup protection

When Home Assistant restarts, all integrations need a moment to reconnect their devices. During this window, many entities briefly pass through `unavailable`. Connection Observer waits 60 seconds after HA has fully started before it begins tracking disconnects. This prevents a flood of false alarms every time HA is restarted.

### Persistent storage

All disconnect events are stored in HA's built-in storage system (`~/.homeassistant/.storage/`). Events survive HA restarts and are retained for up to 30 days. This means:

- A device that went offline before a restart still appears in the next scheduled summary
- The offline-count sensor stays accurate across restarts
- Nothing is lost if HA is temporarily shut down

### Watchdog

Every 5 minutes, Connection Observer actively checks whether devices with open disconnect events (i.e. no reconnect recorded yet) are actually still unavailable. If a device has come back online but did not produce a `state_changed` event (which can happen in edge cases), the watchdog catches this and marks the event as resolved. This keeps the offline-count sensor accurate at all times.

---

## 3. Installation

### Via HACS (recommended)

HACS (Home Assistant Community Store) is the recommended way to install custom integrations.

1. Make sure HACS is installed in your Home Assistant instance. If not, follow the [HACS installation guide](https://hacs.xyz/docs/setup/download).
2. Open **HACS → Integrations** in the HA sidebar.
3. Click the **three-dot menu** (top right) → **Custom repositories**.
4. Enter `https://github.com/OleSint/ha-connection-observer` as the URL and select **Integration** as the category. Click **Add**.
5. Search for **Connection Observer** in the HACS integration list and click **Download**.
6. **Restart Home Assistant.**
7. After the restart, go to **Settings → Devices & Services → Add Integration** and search for **Connection Observer**.

### Manual installation

1. Download the latest release from the [GitHub releases page](https://github.com/OleSint/ha-connection-observer/releases).
2. Extract the archive and copy the folder `custom_components/connection_observer` into your HA configuration directory at `config/custom_components/connection_observer`.
3. **Restart Home Assistant.**
4. After the restart, go to **Settings → Devices & Services → Add Integration** and search for **Connection Observer**.

---

## 4. Setup wizard

The setup wizard walks you through six steps. All settings can be changed afterwards via the **Configure** button on the integration card.

### Step 1 – Labels

**Connection Observer has automatically created three labels in your HA instance during setup.**

This step is informational only — no input required. Simply click Submit to continue.

The labels are immediately visible under **Settings → Labels**:

| Label | Meaning |
|---|---|
| `observer_critical` | Critical – no delay, no cooldown. Immediate alert regardless of all settings. Marked with 🔴 in summaries. |
| `observer_watch` | Watch – normal monitoring according to global settings. |
| `observer_ignore` | Ignore – full exclusion from all monitoring. |

Assign a label to any entity of the desired device — Connection Observer picks it up immediately, no restart or config change needed. Details in [Section 5 – Observer labels](#observer-labels).

### Step 2 – Protocols

**What you select here determines which devices are monitored.**

The wizard only shows integration families that are actually configured in your HA instance. If you have ZHA and ESPHome set up, only those two will appear — there is no need to scroll through a list of 100 unsupported entries.

> **Note:** Protocol selection is optional. If you want to monitor exclusively via the [label system](#observer-labels), you can leave this step empty and click Submit.

| Field | Description |
|---|---|
| **Protocols to monitor** | Multi-select, optional. Choose one or more integration families. Every device belonging to a selected integration is automatically monitored. |
| **Notification language** | Choose English, Deutsch, Français, Nederlands, or Español. This controls the language of all notification messages. |

> **Tip:** You can always come back and add or remove protocols later. Newly added devices in a selected protocol are automatically picked up — no reconfiguration needed.

> **Zigbee2MQTT users:** Zigbee2MQTT devices appear in HA under the `mqtt` integration domain — there is no separate Zigbee2MQTT entry. Select **MQTT** to monitor them. Note that this will also include any other MQTT-based devices in your setup (e.g. Tasmota, custom sensors). For finer control, use the [label system](#observer-labels): assign `observer_watch` to the specific MQTT devices you want to monitor.
>
> ⚠️ **Important:** Connection Observer only detects devices when HA marks them as `unavailable`. Zigbee2MQTT does **not** do this by default — availability checks must be enabled: **Zigbee2MQTT → Settings → Availability → enabled**. Without this setting, Connection Observer cannot detect Z2M devices going offline.

### Step 3 – Notifications

**Configure how and when you receive alerts.**

| Field | Description |
|---|---|
| **Notification service(s)** | Multi-select. Choose one or more `notify.*` services. All selected services receive every notification. You can also type a service name manually. |
| **Immediate notification on disconnect** | If enabled, a notification is sent the moment a device goes offline (subject to alert delay and cooldown settings). Default: **off**. |
| **Scheduled summary** | If enabled, a summary notification is sent at the configured time on the configured days. Default: **on**. |
| **Summary time** | Time of day for the summary notification. |
| **Summary days** | Days of the week on which the summary should be sent. Multiple days can be selected. Default: every day. |
| **Notify on reconnect** | Opt-in. If enabled, a notification is sent when a device comes back online. Default: **off**. |

### Step 4 – Test

An optional test step sends a notification to all your selected services so you can verify everything is connected correctly.

- Check **Send test notification now** (pre-checked) and click Submit to send the test.
- Uncheck it to skip the test and proceed directly.
- If the test fails (e.g. the service is not reachable), an error is shown and you can try again or uncheck the box to proceed anyway.

### Step 5 – Advanced

**All fields in this step are optional. Setting a value to 0 disables that feature.**  
The **global alert delay** set here applies to all protocols unless overridden in Step 6.

| Field | Description |
|---|---|
| **Alert delay** | Minutes a device must be continuously offline before an event is created. A device that reconnects within the delay window produces no event and no notification. Default: **0** (instant). |
| **Cooldown** | Minimum number of minutes between immediate notifications for the same device. The event is always recorded; only the notification is suppressed during the cooldown. Default: **0** (no limit). |
| **Minimum offline duration for summary** | Events shorter than this duration (in minutes) are excluded from the summary. Unlike alert delay, short events *are* still recorded internally. Default: **0** (all events). |
| **Include room / area** | If enabled, the HA area assigned to the device is included in notifications. Default: **off**. |
| **Include manufacturer & model** | If enabled, device info from the device registry is appended to immediate notifications. Default: **off**. |
| **Excluded entity domains** | Exclude entire entity domains from monitoring (e.g. `sensor`, `button`). Select from the list or type a custom domain. `device_tracker` entities are always excluded automatically and do not need to be added here. |
| **Excluded devices** | A list of specific devices to exclude from monitoring entirely. Only devices that have at least one entity on a configured protocol are shown — virtual services (HACS, Supervisor, Add-ons, etc.) do not appear. If a device is added while it is currently offline, it is immediately removed from the offline list and any open HA Repairs issue is resolved. |

### Step 6 – Expert

**Both fields are optional. Skip this step if you only need the global delay.**

#### Per-protocol alert delays

Each protocol you selected in Step 2 appears here with its own delay field. A value of **0** means "use the global alert delay from Step 5". Set a positive value to override the global delay for that specific protocol.

**Tip: Apply recommended delays**  
Check the **Apply recommended delays for all protocols** box and click Submit. All delay fields are pre-filled with the recommended values for each protocol. You can then adjust individual values or accept them as-is.

Recommended values are based on typical connection characteristics of each protocol family:
- Direct TCP protocols (ESPHome, Shelly, Tasmota) → **2 min** (persistent connection, fast detection)
- Local mesh protocols (ZHA, Z-Wave JS) → **5 min** (mesh re-routing takes a moment)
- Passive BLE (BTHome, GARDENA Bluetooth) → **20 min** (rare advertisement cycles)
- Cloud protocols (Tuya, Nest, Ring, Tibber…) → **10 min** (polling latency)

See the [full reference table](#per-protocol-alert-delays) in Section 5 for all values.

#### Watch label – custom offline indicators

Enter the name of an HA label here (e.g. `offline_indicator`). Any entity you assign this label to in the Home Assistant label editor will be treated as a custom offline indicator by Connection Observer:

- When the entity's state turns **`on`** → Connection Observer creates an offline event (protocol shown as `custom`)
- When the entity's state turns **`off`** → Connection Observer marks the device as back online

This is intentionally generic: label any entity you like — a template binary sensor, a helper, or any binary entity — and Connection Observer will react to its state changes.

**Typical use case:** passive BLE devices (BTHome sensors, GARDENA Bluetooth) cannot be monitored in real time via the `unavailable` state. See [Known limitations](#13-known-limitations) and [Watch label](#watch-label--custom-offline-indicators) in Section 5 for a full step-by-step example.

---

## 5. Configuration options

All settings from the setup wizard can be changed at any time via **Settings → Devices & Services → Connection Observer → Configure**.

In addition to the wizard settings, the options page also exposes:

### Test notification

After saving your settings you are taken to a brief test step. Tick **Send test notification now** and click Submit to send a live test to all configured services. Untick to skip. This is useful whenever you change your notification services.

### Domain exclusions

Entire entity domains can be excluded in the options page (same as in the Advanced wizard step). `device_tracker` is always excluded automatically regardless of this setting.

### HA Repairs threshold

Set the number of hours a device must be offline before a persistent issue is created in **Settings → Repairs**. Set to `0` to disable. Default: **24 hours**.

See [Section 7](#7-ha-repairs-integration) for details.

### Notification templates

Seven optional text fields let you override the default notification format for any notification type. Leave a field empty to use the language-appropriate default.

See [Section 6](#6-notification-templates) for details.

### Observer labels

Connection Observer automatically creates three labels in Home Assistant during setup. They are immediately visible under **Settings → Labels** and can be assigned to any entity — no restart or config change required.

| Label | Colour | Behaviour |
|---|---|---|
| `observer_critical` | 🔴 Red | No delay, no cooldown — immediate alert regardless of all global settings. Marked with 🔴 in summaries. Bypasses the flood buffer. |
| `observer_watch` | 🔵 Blue | Normal monitoring according to the global settings (delay, cooldown, etc.). |
| `observer_ignore` | ⚫ Grey | Full exclusion — the device is completely ignored by Connection Observer. |

**Priority:** `observer_ignore` > `observer_critical` > `observer_watch` > protocol-based monitoring

**Conflicts:** If a device has both `observer_ignore` and `observer_critical` or `observer_watch`, `observer_ignore` always wins. A warning appears in the next summary.

**Key properties:**
- A label on **any single entity** of the device is enough — the whole device is treated accordingly.
- Labels take effect **immediately** and **independently of protocol selection**.
- Devices can be covered by both protocols and labels simultaneously — the label takes priority.

> **Tip:** Assign `observer_critical` to safety-critical devices (water sensors, smoke detectors), use `observer_ignore` to silence noisy devices, and use `observer_watch` to monitor individual devices without enabling a whole protocol.

### Per-protocol alert delays

Each selected protocol can have its own alert delay that overrides the global value. Set a protocol's delay to **0** (or leave it absent) to fall back to the global delay.

**One-click setup:** In the Expert step (wizard) or Expert page (options), check **Apply recommended delays** and click Submit. All fields are pre-filled automatically.

| Protocol | Domain | Recommended delay | Reason |
|---|---|---:|---|
| Zigbee (ZHA) | `zha` | 5 min | Mesh routing takes a moment |
| Zigbee (deCONZ) | `deconz` | 5 min | Mesh routing takes a moment |
| Z-Wave (Z-Wave JS) | `zwave_js` | 5 min | Mesh routing takes a moment |
| Matter | `matter` | 5 min | Mesh-like behaviour |
| Thread (OTBR) | `otbr` | 5 min | Thread mesh |
| Bluetooth | `bluetooth` | 10 min | BLE connection setup is slower |
| BTHome | `bthome` | 20 min | Passive BLE – rare advertisements |
| RFXtrx (433 MHz) | `rfxtrx` | 10 min | One-way RF, no acknowledgement |
| MySensors | `mysensors` | 10 min | Slow polling |
| Insteon | `insteon` | 5 min | Proprietary bus, polling-based |
| KNX | `knx` | 5 min | Wired bus, reliable but polled |
| Velbus | `velbus` | 5 min | Wired bus |
| ESPHome | `esphome` | 2 min | Persistent TCP, very fast detection |
| Shelly | `shelly` | 2 min | Persistent TCP, very fast detection |
| Tasmota | `tasmota` | 2 min | Persistent TCP, very fast detection |
| Tuya | `tuya` | 5 min | Cloud polling |
| WLED | `wled` | 2 min | Local TCP |
| TP-Link (Kasa/Tapo) | `tplink` | 3 min | Local TCP |
| TP-Link Omada | `tplink_omada` | 3 min | Local TCP |
| Broadlink | `broadlink` | 3 min | Local TCP |
| Philips Hue | `hue` | 3 min | Local Hue bridge |
| IKEA TRÅDFRI | `tradfri` | 5 min | IKEA hub can be slow to respond |
| LIFX | `lifx` | 3 min | Local UDP/TCP |
| Nanoleaf | `nanoleaf` | 3 min | Local TCP |
| Yeelight | `yeelight` | 2 min | Local TCP |
| Xiaomi Mi Home | `xiaomi_miio` | 5 min | Local + cloud mix |
| Sonos | `sonos` | 3 min | Local network |
| Google Cast | `cast` | 3 min | Local network |
| Logitech Media Server | `squeezebox` | 5 min | Server-dependent |
| Kodi | `kodi` | 3 min | Local network |
| Plex | `plex` | 5 min | Server-dependent |
| Sony Bravia TV | `braviatv` | 3 min | Local network |
| Samsung TV | `samsungtv` | 3 min | Local network |
| LG webOS TV | `webostv` | 3 min | Local network |
| Android TV / Google TV | `androidtv` | 3 min | Local network |
| Apple TV | `apple_tv` | 3 min | Local network |
| Roku | `roku` | 3 min | Local network |
| Yamaha MusicCast | `yamaha_musiccast` | 3 min | Local network |
| Denon / Marantz AVR | `denon` | 3 min | Local network |
| Onkyo / Pioneer AVR | `onkyo` | 3 min | Local network |
| Logitech Harmony | `harmony` | 5 min | Hub-based |
| Netatmo | `netatmo` | 10 min | Cloud polling, higher latency |
| Tado | `tado` | 10 min | Cloud polling |
| Daikin | `daikin` | 5 min | Local + cloud mix |
| ecobee | `ecobee` | 10 min | Cloud polling |
| Google Nest | `nest` | 10 min | Cloud polling |
| HomeWizard Energy | `homewizard` | 3 min | Local LAN |
| Tibber | `tibber` | 10 min | Cloud API |
| SMA Solar | `sma` | 10 min | Cloud / local Modbus |
| SolarEdge | `solaredge` | 10 min | Cloud polling |
| Fronius | `fronius` | 10 min | Cloud polling |
| Tesla Powerwall | `powerwall` | 5 min | Usually local |
| Nuki Smart Lock | `nuki` | 5 min | BLE bridge / cloud |
| August Smart Lock | `august` | 5 min | Cloud |
| Yale Smart Alarm | `yale_smart_alarm` | 5 min | Cloud |
| Ring | `ring` | 10 min | Cloud camera |
| Blink | `blink` | 10 min | Cloud camera |
| Arlo | `arlo` | 10 min | Cloud camera |
| DoorBird | `doorbird` | 3 min | Local LAN |
| Reolink | `reolink` | 3 min | Local LAN |
| Amcrest | `amcrest` | 3 min | Local LAN |
| Eufy Security | `eufy_security` | 5 min | Cloud |
| SimpliSafe | `simplisafe` | 10 min | Cloud |
| Abode | `abode` | 10 min | Cloud |
| UniFi (Ubiquiti) | `unifi` | 3 min | Local LAN |
| AVM FRITZ!Box | `fritz` | 5 min | Local LAN |
| MikroTik | `mikrotik` | 3 min | Local LAN |
| ASUS Router | `asusrouter` | 3 min | Local LAN |
| Synology NAS | `synology_dsm` | 3 min | Local LAN |
| Viessmann ViCare | `vicare` | 10 min | Cloud |
| Vaillant (myVaillant) | `vaillant` | 10 min | Cloud |
| Bosch Smart Home | `bosch_shc` | 5 min | Local controller |
| Mitsubishi MelCloud | `melcloud` | 10 min | Cloud |
| NIBE heat pump | `nibe_heatpump` | 10 min | Cloud / local |
| Huawei Solar | `huawei_solar` | 5 min | Local Modbus |
| Enphase Envoy | `enphase_envoy` | 5 min | Local LAN |
| GoodWe | `goodwe` | 10 min | Cloud |
| Growatt | `growatt_server` | 10 min | Cloud |
| EcoFlow | `ecoflow` | 10 min | Cloud |
| Roborock | `roborock` | 3 min | Local + cloud |
| ECOVACS | `ecovacs` | 5 min | Cloud |
| Neato Robotics | `neato` | 5 min | Cloud |
| LG ThinQ | `lg_thinq` | 5 min | Cloud |
| Meross | `meross` | 3 min | Local + cloud |
| Belkin WeMo | `wemo` | 3 min | Local LAN |
| myQ (Chamberlain / LiftMaster) | `myq` | 5 min | Cloud |
| Nice G.O. | `nice_go` | 5 min | Cloud |
| Ecowitt | `ecowitt` | 10 min | Local but rarely critical |
| Ambient Weather Station | `ambient_station` | 10 min | Cloud / local |
| Husqvarna Automower | `husqvarna_automower` | 10 min | Cloud |
| GARDENA Bluetooth | `gardena_bluetooth` | 20 min | Passive BLE |
| MQTT | `mqtt` | 5 min | Adjust per device – varies widely |
| HomeKit Controller | `homekit_controller` | 5 min | Local HomeKit |
| Lutron Caséta | `lutron_caseta` | 3 min | Local bridge |
| SwitchBot | `switchbot` | 10 min | BLE / cloud |
| iRobot Roomba | `roomba` | 5 min | Cloud |

> ⚠️ **For developers:** Whenever a new protocol is added to `KNOWN_PROTOCOLS` in `const.py`, a matching recommended delay **must** be added to `PROTOCOL_DELAY_HINTS` in the same file, and a new row must be added to this table in all five language documentation files.

---

### Watch label – custom offline indicators

The **watch label** feature lets you monitor *any* device that Connection Observer cannot monitor via the standard `unavailable` path — for example:

- **Passive BLE sensors** (BTHome, GARDENA Bluetooth): no persistent connection, HA only sets `unavailable` after hours
- **Cloud devices** that stay "available" even when the physical device is broken or unreachable
- **Any custom scenario** where you can build a binary sensor that reflects the true connection state

#### How it works

1. Create a **template binary sensor** (or any binary entity) that turns `on` when your device is offline and `off` when it is online.
2. In the HA label editor (**Settings → Labels**), create a label with the exact name you configured in the Expert step (e.g. `offline_indicator`).
3. Assign that label to your template binary sensor.
4. Connection Observer automatically picks up all entities carrying the label and monitors their state:
   - `on` → creates an offline event (protocol shown as `custom`)
   - `off` → marks the device as back online

#### Example: BTHome door sensor freshness monitor

Create a template binary sensor that checks whether the last update was more than 2 hours ago:

```yaml
# configuration.yaml
template:
  - binary_sensor:
      - name: "BTHome Door Offline Indicator"
        unique_id: bthome_door_offline_indicator
        state: >
          {{ (now() - states.sensor.bthome_door_contact.last_updated).total_seconds() > 7200 }}
        device_class: problem
```

Then:
1. Go to **Settings → Labels** → create a label named `offline_indicator`
2. Go to **Settings → Devices & Services → Entities** → find `binary_sensor.bthome_door_offline_indicator` → assign the label `offline_indicator`
3. In Connection Observer's Expert step, set **Watch label** to `offline_indicator`

Connection Observer will now create an offline event whenever the BTHome sensor has not reported for more than 2 hours, and will close it automatically when a new report arrives.

> **Tip:** You can label multiple entities with the same watch label. Each one is monitored independently. The device name shown in notifications is the friendly name of the labelled entity.

---

### Recommended starting configuration

- **Immediate notification:** off
- **Summary:** on, daily at 08:00, every day
- **Alert delay:** 5 minutes global (avoids false alarms from brief WiFi dropouts)
- **Per-protocol delays:** use "Apply recommended delays" for a quick setup
- **Min. offline duration:** 5 minutes (keeps the summary clean)
- **Include area:** on (makes notifications much more readable)
- **HA Repairs threshold:** 24 hours (creates a repair issue for persistent problems)
- **Watch label:** set up for any passive BLE or custom devices you want to monitor

---

## 6. Notification templates

Connection Observer sends three types of notifications: immediate (disconnect), reconnect, and summary. Each type has a title and a message body that can be customised independently.

### Available templates

All template fields are in **Settings → Devices & Services → Connection Observer → Configure**, at the bottom of the options page. Leave any field empty to use the language-default text.

| Template key | Applies to | Available variables |
|---|---|---|
| `tmpl_imm_title` | Immediate notification — title | `{device_name}` `{protocol}` `{time}` `{area}` `{model}` |
| `tmpl_imm_msg` | Immediate notification — message body | `{device_name}` `{protocol}` `{time}` `{area}` `{model}` |
| `tmpl_rec_title` | Reconnect notification — title | `{device_name}` |
| `tmpl_rec_msg` | Reconnect notification — message body | `{device_name}` |
| `tmpl_sum_title` | Summary notification — title | `{count}` |
| `tmpl_sum_resolved` | Summary — one line per resolved event | `{device_name}` `{area}` `{protocol}` `{time_offline}` `{time_online}` |
| `tmpl_sum_ongoing` | Summary — one line per still-offline device | `{device_name}` `{area}` `{protocol}` `{time_offline}` |

### Variable notes

- `{area}` is pre-formatted as ` [Room Name]` (with a leading space) when the *include area* option is on, or as an empty string when it is off. You can place it directly after `{device_name}` without adding a space.
- `{model}` is `Manufacturer – Model` or empty if device info is unknown or the *include device info* option is off.
- `{time}` / `{time_offline}` / `{time_online}` are formatted as `HH:MM`. The date is included in `{time_offline}` for the summary (format: `MM/DD HH:MM` for English, `DD.MM. HH:MM` for German).

### Example custom templates

**Compact immediate message (English):**
```
Title: 🔴 {device_name} offline
Message: {device_name} ({protocol}) lost connection at {time}{area}.
```

**German summary line with custom format:**
```
tmpl_sum_ongoing: ❌ {device_name}{area} via {protocol} – seit {time_offline} offline
```

### Important notes

- If you set a custom `tmpl_imm_msg`, the automatic second line with area and device model (📍 …) is **not** appended. Include `{area}` and `{model}` in your template if you want that information.
- Template errors (e.g. a typo in a variable name) are logged as warnings and the raw template string is used as-is.

---

## 7. HA Repairs integration

When a device has been continuously offline for longer than the configured threshold (default: 24 hours), Connection Observer creates a persistent issue in **Settings → Repairs**. This is in addition to (not instead of) the regular notifications.

### What the repair issue shows

The issue displays:
- The device name
- The protocol / integration it belongs to
- The timestamp when it went offline

### Automatic resolution

When the device comes back online — either through a `state_changed` event or via the watchdog — the repair issue is **automatically deleted**. No manual action required.

### Disabling

Set **HA Repairs issue after N hours offline** to `0` in the options to disable this feature entirely.

---

## 8. Entities

Connection Observer creates three entities per integration instance.

### `sensor.connection_observer_offline_devices`

**Type:** Sensor | **Unit:** devices | **Icon:** `mdi:lan-disconnect`

Shows the number of devices that are currently offline.

**State attributes:**

| Attribute | Description |
|---|---|
| `devices` | Flat list of device names that are currently offline. |
| `by_protocol` | Per-protocol breakdown: offline count and detailed device list per integration family. |

The `by_protocol` attribute has the following structure:

```yaml
by_protocol:
  shelly:
    offline: 1
    devices:
      - name: "Kitchen Plug"
        offline_since: "22.05. 14:30"
        offline_duration: "2h 15m"
  bthome:
    offline: 0
    devices: []
```

Only protocols with at least one currently offline device appear in this attribute.

**Example — Markdown card showing per-protocol status:**
```yaml
type: markdown
content: >
  {% set proto = state_attr('sensor.connection_observer_offline_devices', 'by_protocol') %}
  {% for p, data in proto.items() %}
  **{{ p }}**: {{ data.devices | map(attribute='name') | join(', ') }}
  (offline seit {{ data.devices[0].offline_since }})
  {% endfor %}
```

**Example use in an automation:**
```yaml
condition:
  - condition: numeric_state
    entity_id: sensor.connection_observer_offline_devices
    above: 0
```

---

### `sensor.connection_observer_pending_summary_events`

**Type:** Sensor | **Unit:** events | **Icon:** `mdi:clock-alert-outline`

Shows the number of disconnect events not yet included in a summary. Resets to 0 after a summary is sent or after `clear_history` is called.

---

### `sensor.connection_observer_event_history`

**Type:** Sensor | **Unit:** events | **Icon:** `mdi:history`

Shows the total number of stored disconnect events.

**State attribute `events`:** List of the last 100 events, newest first.

```yaml
events:
  - device_name: "Basement Water Sensor"
    area: "Basement"
    protocol: "zha"
    disconnected_at: "2026-06-10T07:15:00+02:00"
    reconnected_at: "2026-06-10T07:42:00+02:00"
    still_offline: false
    is_critical: true
  - device_name: "Bedroom Bulb"
    area: "Bedroom"
    protocol: "hue"
    disconnected_at: "2026-06-10T09:05:00+02:00"
    reconnected_at: null
    still_offline: true
    is_critical: false
```

Designed for dashboard cards like **flex-table-card** or **mushroom-template-card** to visualise per-device connection history.

---

### `binary_sensor.connection_observer_connection_problem`

**Type:** Binary Sensor | **Device class:** `problem` | **Icon:** `mdi:check-network`

- **`ON`** – at least one device is currently offline
- **`OFF`** – all monitored devices are reachable

**Example use — alert when problem persists for more than 10 minutes:**
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
      message: "A device has been offline for more than 10 minutes!"
```

---

## 9. Services

### `connection_observer.send_summary_now`

Immediately sends a summary of all pending disconnect events. After calling this service, all pending events are marked as included in a summary.

```yaml
service: connection_observer.send_summary_now
```

---

### `connection_observer.clear_history`

Clears all stored disconnect events from memory and persistent storage. Also removes any open HA Repairs issues.

> ⚠️ This action is irreversible.

```yaml
service: connection_observer.clear_history
```

---

### `connection_observer.clear_device`

Removes all stored disconnect events for a **single device** and resolves any open HA Repairs issue for it. All other devices are unaffected.

Pass any entity that belongs to the device you want to clear.

**When to use this:**
- After a planned maintenance on one specific device
- To manually close a stale offline event for a single device without wiping everything

```yaml
service: connection_observer.clear_device
data:
  entity_id: light.living_room_bulb
```

---

## 10. Notification formats

### Immediate notification

**Basic:**
> **Connection Lost**
> ⚠️ Living Room Plug (shelly) lost connection at 14:32.

**With area and device info enabled:**
> **Connection Lost**
> ⚠️ Living Room Plug (shelly) lost connection at 14:32.
> 📍 Living Room  ·  Shelly Plus 1PM

### Reconnect notification (opt-in)

> **Connection Restored**
> ✅ Living Room Plug is back online.

### Flood notification (≥ 5 devices simultaneously)

When 5 or more devices disconnect within 5 seconds, a single grouped notification is sent instead of individual alerts. This prevents notification floods during router reboots or brief infrastructure outages.

**Disconnect flood:**
> **Connection Outage – 8 devices**
> ⚠️ 8 devices went offline simultaneously — likely an infrastructure issue (e.g. router restart).
> • Living Room Plug (shelly)
> • Kitchen Sensor (zha)
> • Hallway Light (hue)
> • Bedroom Bulb (hue)
> • Office Switch (esphome)
> • …

**Reconnect flood:**
> **Connection Restored – 8 devices**
> ✅ 8 devices came back online:
> • Living Room Plug
> • Kitchen Sensor
> • Hallway Light
> • Bedroom Bulb
> • Office Switch
> • …

If fewer than 5 devices are affected, individual notifications continue to be sent as usual (including cooldown checks).

### Summary notification

> **Connection Summary**
> 📋 3 device(s) affected since last summary:
> • 🔴 Basement Water Sensor [Basement] (zha): offline since 05/19 07:15, back online at 07:42
> • Bedroom Bulb [Bedroom] (hue): offline since 05/19 09:05 ⚠️ still offline
> • Hallway Motion (esphome): offline since 05/19 11:20, back online at 11:28

The 🔴 prefix marks devices labelled `observer_critical`.

---

## 11. Advanced use cases

### Using both immediate and summary mode together

Enable both modes simultaneously:
- Set **alert delay** to 3–5 minutes so brief dropouts are ignored
- Enable **immediate notification** for real-time awareness
- Enable **summary** for a daily overview
- Set **minimum offline duration** to 5 minutes in the summary to only show meaningful events

### Combining with HA automations

```yaml
# Announce offline devices via TTS if still offline at bedtime
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
        Warning: {{ states('sensor.connection_observer_offline_devices') }}
        device(s) are currently offline.
```

### Sending to multiple services

Select multiple services in the notification service field. All services receive every notification simultaneously.

### Excluding a specific device

Add it to the *Excluded devices* list in the Advanced settings. All entities of that device will be ignored. If the device is currently offline when you save, it is immediately removed from the offline list and any open HA Repairs issue is resolved automatically.

### Using Observer labels for fine-grained control

The label system provides per-device exceptions without ever opening the configuration:

**Safety-critical device (e.g. water sensor, smoke detector):**  
Assign `observer_critical` to any entity of the device → immediate alert, no delay, no cooldown, 🔴 in summaries.

**Temporarily exclude a device (e.g. during renovation):**  
Assign `observer_ignore` → device is fully silenced. Remove the label when you are done.

**Monitor one specific MQTT device without enabling all of MQTT:**  
Assign `observer_watch` → only that device is picked up.

---

## 12. Troubleshooting

### No notifications are being sent

1. Check that a notification service is selected under **Configure**.
2. Test your notify service directly via **Developer Tools → Services**.
3. Check the HA log for `connection_observer` errors.
4. Make sure **Immediate notification** or **Scheduled summary** is enabled.

### The summary is not being sent

1. Verify **Scheduled summary** is enabled.
2. Check summary time and days under **Configure**.
3. Check `sensor.connection_observer_pending_summary_events` — if it is 0, no events are pending and no summary will be sent.
4. Check the HA log.

### Devices show as offline after HA restart

This should not happen due to the 60-second startup grace period. If it does:
- The device may genuinely be offline.
- If the state is not `unavailable` in HA, the watchdog will correct the event within 5 minutes.

### A device shows as offline but is fine in HA

The watchdog runs every 5 minutes and will automatically close the event. You can also call `clear_history` to reset immediately.

### The HA Repairs issue was not created

1. Check that **HA Repairs threshold** is not set to `0`.
2. The device must be continuously offline for longer than the threshold — the watchdog creates the issue during its periodic run (every 5 minutes), so there may be a short delay after the threshold is crossed.

---

## 13. Known limitations

- **Cloud-only integrations:** Devices that connect exclusively through a cloud service may not be detected if the integration does not set entities to `unavailable` when the cloud is unreachable.
- **Polling integrations:** A disconnect may only be detected after the next poll cycle, introducing a short delay.
- **Passive BLE devices (BTHome etc.):** Bluetooth Low Energy sensors such as BTHome door/window sensors do not maintain a persistent connection — they broadcast periodic advertisements. If such a device goes offline (e.g. battery removed), Home Assistant only sets its entities to `unavailable` after its own internal timeout, which can be several hours. Connection Observer can only react once HA reports `unavailable`, so real-time detection is not possible via the standard path. **Solution (v1.1.0):** Use the [watch label feature](#watch-label--custom-offline-indicators) to build a template sensor that tracks the last-seen timestamp and label it — Connection Observer then monitors *that* sensor instead of the raw `unavailable` state.
- **Zigbee2MQTT – availability checks required:** Connection Observer reacts to the `unavailable` state of entities. Zigbee2MQTT does **not** set this state by default — availability checks must be enabled in Z2M: **Settings → Availability → enabled**. Without this setting, Z2M devices will not be detected.
- **One instance only:** Connection Observer supports a single integration instance per HA installation.
- **30-day event retention:** Events older than 30 days are automatically pruned from storage.
