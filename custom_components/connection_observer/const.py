"""Constants for Connection Observer."""

DOMAIN = "connection_observer"

# Known protocol/integration domains with friendly labels.
# Only entries whose domain is actually configured in the HA instance
# will appear in the setup wizard — so a large list has no runtime cost.
KNOWN_PROTOCOLS: dict[str, str] = {
    # ── Mesh / radio protocols ────────────────────────────────────────────
    "zha": "Zigbee (ZHA)",
    "deconz": "Zigbee (deCONZ)",
    "zwave_js": "Z-Wave (Z-Wave JS)",
    "matter": "Matter",
    "otbr": "Thread (OTBR)",
    "bluetooth": "Bluetooth",
    "bthome": "BTHome",
    "rfxtrx": "RFXtrx (433 MHz)",
    "mysensors": "MySensors",
    "insteon": "Insteon",
    "knx": "KNX",
    "velbus": "Velbus",
    # ── WiFi / LAN device integrations ───────────────────────────────────
    "esphome": "ESPHome",
    "shelly": "Shelly",
    "tasmota": "Tasmota",
    "tuya": "Tuya",
    "wled": "WLED",
    "tplink": "TP-Link (Kasa/Tapo)",
    "tplink_omada": "TP-Link Omada",
    "broadlink": "Broadlink",
    # ── Lighting ─────────────────────────────────────────────────────────
    "hue": "Philips Hue",
    "tradfri": "IKEA TRÅDFRI",
    "lifx": "LIFX",
    "nanoleaf": "Nanoleaf",
    "yeelight": "Yeelight",
    "xiaomi_miio": "Xiaomi (Mi Home / Yeelight)",
    # ── Speakers & media ─────────────────────────────────────────────────
    "sonos": "Sonos",
    "cast": "Google Cast (Chromecast)",
    "squeezebox": "Logitech Media Server",
    "kodi": "Kodi",
    "plex": "Plex",
    "braviatv": "Sony Bravia TV",
    "samsungtv": "Samsung TV",
    "webostv": "LG webOS TV",
    "androidtv": "Android TV / Google TV",
    "apple_tv": "Apple TV",
    "roku": "Roku",
    "yamaha_musiccast": "Yamaha MusicCast",
    "denon": "Denon / Marantz AVR",
    "onkyo": "Onkyo / Pioneer AVR",
    "harmony": "Logitech Harmony",
    # ── Climate & energy ─────────────────────────────────────────────────
    "netatmo": "Netatmo",
    "tado": "Tado",
    "daikin": "Daikin",
    "ecobee": "ecobee",
    "nest": "Google Nest",
    "homewizard": "HomeWizard Energy",
    "tibber": "Tibber",
    "sma": "SMA Solar",
    "solaredge": "SolarEdge",
    "fronius": "Fronius",
    "powerwall": "Tesla Powerwall",
    # ── Security & access ────────────────────────────────────────────────
    "nuki": "Nuki Smart Lock",
    "august": "August Smart Lock",
    "yale_smart_alarm": "Yale Smart Alarm",
    "ring": "Ring",
    "blink": "Blink",
    "arlo": "Arlo",
    "doorbird": "DoorBird",
    "reolink": "Reolink",
    "amcrest": "Amcrest",
    "eufy_security": "Eufy Security",
    "simplisafe": "SimpliSafe",
    "abode": "Abode",
    # ── Network & infrastructure ─────────────────────────────────────────
    "unifi": "UniFi (Ubiquiti)",
    "fritz": "AVM FRITZ!Box",
    "mikrotik": "MikroTik",
    "asusrouter": "ASUS Router",
    "synology_dsm": "Synology NAS",
    # ── Heating / HVAC ───────────────────────────────────────────────────
    "vicare": "Viessmann ViCare",
    "vaillant": "Vaillant (myVaillant)",
    "bosch_shc": "Bosch Smart Home",
    "melcloud": "Mitsubishi MelCloud",
    "nibe_heatpump": "NIBE Wärmepumpe",
    # ── Solar / energy (extended) ────────────────────────────────────────
    "huawei_solar": "Huawei Solar",
    "enphase_envoy": "Enphase Envoy",
    "goodwe": "GoodWe",
    "growatt_server": "Growatt",
    "ecoflow": "EcoFlow",
    # ── Vacuum robots ────────────────────────────────────────────────────
    "roborock": "Roborock",
    "ecovacs": "ECOVACS",
    "neato": "Neato Robotics",
    # ── Household appliances ─────────────────────────────────────────────
    "lg_thinq": "LG ThinQ",
    "meross": "Meross",
    "wemo": "Belkin WeMo",
    # ── Gates & garage doors ─────────────────────────────────────────────
    "myq": "myQ (Chamberlain / LiftMaster)",
    "nice_go": "Nice G.O.",
    # ── Local weather stations ───────────────────────────────────────────
    "ecowitt": "Ecowitt",
    "ambient_station": "Ambient Weather Station",
    # ── Garden & household ───────────────────────────────────────────────
    "husqvarna_automower": "Husqvarna Automower",
    "gardena_bluetooth": "GARDENA Bluetooth",
    # ── Other / generic ──────────────────────────────────────────────────
    "mqtt": "MQTT",
    "homekit_controller": "HomeKit Controller",
    "lutron_caseta": "Lutron Caséta",
    "switchbot": "SwitchBot",
    "roomba": "iRobot Roomba",
}

# Recommended alert delay (minutes) per protocol.
# ⚠️  Whenever a new entry is added to KNOWN_PROTOCOLS, a matching entry
#     MUST be added here as well so the config-flow hint stays complete.
PROTOCOL_DELAY_HINTS: dict[str, int] = {
    # ── Mesh / radio ─────────────────────────────────────────────────────
    "zha":               5,   # Zigbee mesh routing takes a moment
    "deconz":            5,   # Zigbee mesh routing takes a moment
    "zwave_js":          5,   # Z-Wave mesh routing takes a moment
    "matter":            5,   # Mesh-like behaviour
    "otbr":              5,   # Thread mesh
    "bluetooth":        10,   # BLE connection setup is slower
    "bthome":           20,   # Passive BLE – rare advertisements
    "rfxtrx":           10,   # One-way 433 MHz RF, no ACK
    "mysensors":        10,   # Slow polling
    "insteon":           5,   # Proprietary bus, polling-based
    "knx":               5,   # Wired bus, reliable but polled
    "velbus":            5,   # Wired bus
    # ── WiFi / LAN – direct TCP ──────────────────────────────────────────
    "esphome":           2,   # Persistent TCP, very fast detection
    "shelly":            2,   # Persistent TCP, very fast detection
    "tasmota":           2,   # Persistent TCP, very fast detection
    "tuya":              5,   # Cloud polling
    "wled":              2,   # Local TCP
    "tplink":            3,   # Local TCP
    "tplink_omada":      3,   # Local TCP
    "broadlink":         3,   # Local TCP
    # ── Lighting ─────────────────────────────────────────────────────────
    "hue":               3,   # Local Hue bridge
    "tradfri":           5,   # IKEA hub can be slow to respond
    "lifx":              3,   # Local UDP/TCP
    "nanoleaf":          3,   # Local TCP
    "yeelight":          2,   # Local TCP
    "xiaomi_miio":       5,   # Local + cloud mix
    # ── Speakers & media ─────────────────────────────────────────────────
    "sonos":             3,   # Local network
    "cast":              3,   # Local network
    "squeezebox":        5,   # Server-dependent
    "kodi":              3,   # Local network
    "plex":              5,   # Server-dependent
    "braviatv":          3,   # Local network
    "samsungtv":         3,   # Local network
    "webostv":           3,   # Local network
    "androidtv":         3,   # Local network
    "apple_tv":          3,   # Local network
    "roku":              3,   # Local network
    "yamaha_musiccast":  3,   # Local network
    "denon":             3,   # Local network
    "onkyo":             3,   # Local network
    "harmony":           5,   # Hub-based
    # ── Climate & energy ─────────────────────────────────────────────────
    "netatmo":          10,   # Cloud polling, higher latency
    "tado":             10,   # Cloud polling
    "daikin":            5,   # Local + cloud mix
    "ecobee":           10,   # Cloud polling
    "nest":             10,   # Cloud polling
    "homewizard":        3,   # Local LAN
    "tibber":           10,   # Cloud API
    "sma":              10,   # Cloud / local Modbus
    "solaredge":        10,   # Cloud polling
    "fronius":          10,   # Cloud polling
    "powerwall":         5,   # Usually local
    # ── Security & access ────────────────────────────────────────────────
    "nuki":              5,   # BLE bridge / cloud
    "august":            5,   # Cloud
    "yale_smart_alarm":  5,   # Cloud
    "ring":             10,   # Cloud camera
    "blink":            10,   # Cloud camera
    "arlo":             10,   # Cloud camera
    "doorbird":          3,   # Local LAN
    "reolink":           3,   # Local LAN
    "amcrest":           3,   # Local LAN
    "eufy_security":     5,   # Cloud
    "simplisafe":       10,   # Cloud
    "abode":            10,   # Cloud
    # ── Network & infrastructure ─────────────────────────────────────────
    "unifi":             3,   # Local LAN
    "fritz":             5,   # Local LAN
    "mikrotik":          3,   # Local LAN
    "asusrouter":        3,   # Local LAN
    "synology_dsm":      3,   # Local LAN
    # ── Heating / HVAC ───────────────────────────────────────────────────
    "vicare":           10,   # Cloud
    "vaillant":         10,   # Cloud
    "bosch_shc":         5,   # Local controller
    "melcloud":         10,   # Cloud
    "nibe_heatpump":    10,   # Cloud / local
    # ── Solar / energy (extended) ────────────────────────────────────────
    "huawei_solar":      5,   # Local Modbus
    "enphase_envoy":     5,   # Local LAN
    "goodwe":           10,   # Cloud
    "growatt_server":   10,   # Cloud
    "ecoflow":          10,   # Cloud
    # ── Vacuum robots ────────────────────────────────────────────────────
    "roborock":          3,   # Local + cloud
    "ecovacs":           5,   # Cloud
    "neato":             5,   # Cloud
    # ── Household appliances ─────────────────────────────────────────────
    "lg_thinq":          5,   # Cloud
    "meross":            3,   # Local + cloud
    "wemo":              3,   # Local LAN
    # ── Gates & garage doors ─────────────────────────────────────────────
    "myq":               5,   # Cloud
    "nice_go":           5,   # Cloud
    # ── Local weather stations ───────────────────────────────────────────
    "ecowitt":          10,   # Local but rarely critical
    "ambient_station":  10,   # Cloud / local
    # ── Garden & household ───────────────────────────────────────────────
    "husqvarna_automower": 10,  # Cloud
    "gardena_bluetooth":   20,  # Passive BLE
    # ── Other / generic ──────────────────────────────────────────────────
    "mqtt":              5,   # Adjust per device – varies widely
    "homekit_controller": 5,  # Local HomeKit
    "lutron_caseta":     3,   # Local bridge
    "switchbot":        10,   # BLE / cloud
    "roomba":            5,   # Cloud
}

# Config keys – notifications
CONF_PROTOCOLS = "protocols"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_IMMEDIATE = "notify_immediate"
CONF_NOTIFY_SUMMARY = "notify_summary"
CONF_SUMMARY_TIME = "summary_time"
CONF_SUMMARY_DAYS = "summary_days"
CONF_NOTIFY_RECONNECT = "notify_reconnect"
CONF_LANGUAGE = "language"

# Config keys – advanced
CONF_EXCLUDED_ENTITIES = "excluded_entities"  # legacy – kept for migration only
CONF_EXCLUDED_DEVICES = "excluded_devices"
CONF_EXCLUDED_DOMAINS = "excluded_domains"
CONF_ALERT_DELAY = "alert_delay"
CONF_COOLDOWN = "cooldown"
CONF_MIN_OFFLINE_DURATION = "min_offline_duration"
CONF_INCLUDE_AREA = "include_area"
CONF_INCLUDE_DEVICE_INFO = "include_device_info"
CONF_REPAIRS_THRESHOLD = "repairs_threshold"  # hours offline before HA Repairs entry, 0 = off

# Config keys – v1.1.0
CONF_PROTOCOL_DELAYS = "protocol_delays"   # dict[str, int]  protocol → delay minutes (overrides global)
CONF_WATCH_LABEL = "watch_label"           # str  HA label name; entities with this label are monitored as custom offline indicators

# Config keys – notification templates (empty string = use language default)
CONF_TMPL_IMM_TITLE = "tmpl_imm_title"
CONF_TMPL_IMM_MSG = "tmpl_imm_msg"
CONF_TMPL_REC_TITLE = "tmpl_rec_title"
CONF_TMPL_REC_MSG = "tmpl_rec_msg"
CONF_TMPL_SUM_TITLE = "tmpl_sum_title"
CONF_TMPL_SUM_LINE_RESOLVED = "tmpl_sum_resolved"
CONF_TMPL_SUM_LINE_ONGOING = "tmpl_sum_ongoing"

# Storage
STORAGE_KEY = f"{DOMAIN}_events"
STORAGE_VERSION = 1

# Languages
LANG_EN = "en"
LANG_DE = "de"
LANG_FR = "fr"
LANG_NL = "nl"
LANG_ES = "es"

# Timing
STARTUP_GRACE_SECONDS = 60
WATCHDOG_INTERVAL_SECONDS = 300
