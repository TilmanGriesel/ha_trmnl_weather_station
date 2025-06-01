"""Constants for the TRMNL Weather Station Push integration."""

DOMAIN = "trmnl_weather_station"
CONF_URL = "url"
CONF_PRIORITY_SENSORS = "priority_sensors"
CONF_STATION_KEYWORD = "station_keyword"
CONF_PRIMARY_CO2 = "primary_co2_filter"  # TODO: Remove me
CONF_DEVICES = "devices"
CONF_INCLUDE_OUTDOOR = "include_outdoor"

DEFAULT_URL = (
    "https://usetrmnl.com/api/custom_plugins/XXXX-XXXX-XXXX-XXXX"  # Example URL
)
MIN_TIME_BETWEEN_UPDATES = 1800  # 1800 is every 30 mins
DEFAULT_STATION_KEYWORD = "weather_station"

# API limit for TRMNL
MAX_PAYLOAD_SIZE = 2048  # 2KB max payload size

DEFAULT_WEATHER_DOMAINS = ["weather_station"]
OUTDOOR_KEYWORDS = [
    "outdoor",
    "outside",
    "exterior",
    "garden",
    "patio",
    "balcony",
    "terrace",
    "yard",
]

TOP_PRIORITY_SENSORS = [
    "carbon_dioxide",
    "temperature",
    "humidity",
]

PRIORITY_SENSORS = TOP_PRIORITY_SENSORS + [
    "pressure",
    "rain",
    "wind_strength",
]
