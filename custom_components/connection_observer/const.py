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
CONF_EXCLUDED_ENTITIES = "excluded_entities"
CONF_EXCLUDED_DOMAINS = "excluded_domains"
CONF_ALERT_DELAY = "alert_delay"
CONF_COOLDOWN = "cooldown"
CONF_MIN_OFFLINE_DURATION = "min_offline_duration"
CONF_INCLUDE_AREA = "include_area"
CONF_INCLUDE_DEVICE_INFO = "include_device_info"
CONF_REPAIRS_THRESHOLD = "repairs_threshold"  # hours offline before HA Repairs entry, 0 = off

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
