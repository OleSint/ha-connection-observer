# Connection Observer – Documentation

**Version:** 1.0.2  
**Repository:** [github.com/OleSint/ha-connection-observer](https://github.com/OleSint/ha-connection-observer)

---

## Table of Contents

1. [What is Connection Observer?](#1-what-is-connection-observer)
2. [How it works](#2-how-it-works)
3. [Installation](#3-installation)
4. [Setup wizard](#4-setup-wizard)
5. [Configuration options](#5-configuration-options)
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

The setup wizard walks you through four steps. All settings can be changed afterwards via the **Configure** button on the integration card.

### Step 1 – Protocols

**What you select here determines which devices are monitored.**

The wizard only shows integration families that are actually configured in your HA instance. If you have ZHA and ESPHome set up, only those two will appear — there is no need to scroll through a list of 100 unsupported entries.

| Field | Description |
|---|---|
| **Protocols to monitor** | Multi-select. Choose one or more integration families. Every device belonging to a selected integration is automatically monitored. |
| **Notification language** | Choose English, Deutsch, Français, Nederlands, or Español. This controls the language of all notification messages. |

> **Tip:** You can always come back and add or remove protocols later. Newly added devices in a selected protocol are automatically picked up — no reconfiguration needed.

### Step 2 – Notifications

**Configure how and when you receive alerts.**

| Field | Description |
|---|---|
| **Notification service(s)** | Multi-select. Choose one or more `notify.*` services. All selected services receive every notification. You can also type a service name manually. |
| **Immediate notification on disconnect** | If enabled, a notification is sent the moment a device goes offline (subject to alert delay and cooldown settings). Default: **off**. |
| **Scheduled summary** | If enabled, a summary notification is sent at the configured time on the configured days. Default: **on**. |
| **Summary time** | Time of day for the summary notification. |
| **Summary days** | Days of the week on which the summary should be sent. Multiple days can be selected. Default: every day. |
| **Notify on reconnect** | Opt-in. If enabled, a notification is sent when a device comes back online. Default: **off**. |

### Step 3 – Test

An optional test step sends a notification to all your selected services so you can verify everything is connected correctly.

- Check **Send test notification now** (pre-checked) and click Submit to send the test.
- Uncheck it to skip the test and proceed directly.
- If the test fails (e.g. the service is not reachable), an error is shown and you can try again or uncheck the box to proceed anyway.

### Step 4 – Advanced

**All fields in this step are optional. Setting a value to 0 disables that feature.**

| Field | Description |
|---|---|
| **Alert delay** | Minutes a device must be continuously offline before an event is created. A device that reconnects within the delay window produces no event and no notification. Default: **0** (instant). |
| **Cooldown** | Minimum number of minutes between immediate notifications for the same device. The event is always recorded; only the notification is suppressed during the cooldown. Default: **0** (no limit). |
| **Minimum offline duration for summary** | Events shorter than this duration (in minutes) are excluded from the summary. Unlike alert delay, short events *are* still recorded internally. Default: **0** (all events). |
| **Include room / area** | If enabled, the HA area assigned to the device is included in notifications. Default: **off**. |
| **Include manufacturer & model** | If enabled, device info from the device registry is appended to immediate notifications. Default: **off**. |
| **Excluded entity domains** | Exclude entire entity domains from monitoring (e.g. `sensor`, `button`). Select from the list or type a custom domain. `device_tracker` entities are always excluded automatically and do not need to be added here. |
| **Excluded entities** | A list of specific entities to exclude from monitoring. |

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

### Recommended starting configuration

- **Immediate notification:** off
- **Summary:** on, daily at 08:00, every day
- **Alert delay:** 5 minutes (avoids false alarms from brief WiFi dropouts)
- **Min. offline duration:** 5 minutes (keeps the summary clean)
- **Include area:** on (makes notifications much more readable)
- **HA Repairs threshold:** 24 hours (creates a repair issue for persistent problems)

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
| `devices` | List of device names that are currently offline. |

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

### Summary notification

> **Connection Summary**
> 📋 3 device(s) affected since last summary:
> • Kitchen Sensor [Kitchen] (zha): offline since 05/19 07:15, back online at 07:42
> • Bedroom Bulb [Bedroom] (hue): offline since 05/19 09:05 ⚠️ still offline
> • Hallway Motion (esphome): offline since 05/19 11:20, back online at 11:28

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

### Excluding a specific entity

Add it to the *Excluded entities* list in the Advanced settings. The device's other entities remain monitored.

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
- **Bluetooth coverage:** Devices only visible at the raw Bluetooth adapter level may not be covered.
- **One instance only:** Connection Observer supports a single integration instance per HA installation.
- **30-day event retention:** Events older than 30 days are automatically pruned from storage.
