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

# Config keys
CONF_PROTOCOLS = "protocols"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_IMMEDIATE = "notify_immediate"
CONF_NOTIFY_SUMMARY = "notify_summary"
CONF_SUMMARY_TIME = "summary_time"
CONF_SUMMARY_DAYS = "summary_days"
CONF_NOTIFY_RECONNECT = "notify_reconnect"
CONF_LANGUAGE = "language"
CONF_EXCLUDED_ENTITIES = "excluded_entities"

# Storage
STORAGE_KEY = f"{DOMAIN}_events"
STORAGE_VERSION = 1

# Languages
LANG_EN = "en"
LANG_DE = "de"

# Startup grace period in seconds before tracking begins
STARTUP_GRACE_SECONDS = 60
