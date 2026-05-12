"""Constants for Connection Observer."""

DOMAIN = "connection_observer"

# Known protocol/integration domains with friendly labels
KNOWN_PROTOCOLS: dict[str, str] = {
    "zha": "Zigbee (ZHA)",
    "deconz": "Zigbee (deCONZ)",
    "zwave_js": "Z-Wave (Z-Wave JS)",
    "matter": "Matter",
    "bluetooth": "Bluetooth",
    "esphome": "ESPHome (WiFi/BT)",
    "shelly": "Shelly (WiFi)",
    "tasmota": "Tasmota (WiFi)",
    "tuya": "Tuya (WiFi)",
    "wled": "WLED (WiFi)",
    "mqtt": "MQTT",
    "homekit_controller": "HomeKit Controller",
    "xiaomi_miio": "Xiaomi (Mi Home)",
    "otbr": "Thread (OTBR)",
    "lutron_caseta": "Lutron Caséta",
    "insteon": "Insteon",
    "knx": "KNX",
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
