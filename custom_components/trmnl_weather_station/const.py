"""Constants for the TRMNL Weather Station Push integration."""

DOMAIN = "trmnl_weather_station"
CONF_URL = "url"
CONF_CO2_SENSOR = "co2_sensor"
CONF_CO2_NAME = "co2_name"
CONF_SENSOR_1 = "sensor_1"
CONF_SENSOR_1_NAME = "sensor_1_name"
CONF_SENSOR_2 = "sensor_2"
CONF_SENSOR_2_NAME = "sensor_2_name"
CONF_SENSOR_3 = "sensor_3"
CONF_SENSOR_3_NAME = "sensor_3_name"
CONF_SENSOR_4 = "sensor_4"
CONF_SENSOR_4_NAME = "sensor_4_name"
CONF_SENSOR_5 = "sensor_5"
CONF_SENSOR_5_NAME = "sensor_5_name"
CONF_SENSOR_6 = "sensor_6"
CONF_SENSOR_6_NAME = "sensor_6_name"
CONF_INCLUDE_IDS = "include_ids"

DEFAULT_URL = ""
MIN_TIME_BETWEEN_UPDATES = 30
DEFAULT_UPDATE_INTERVAL = 30

MAX_PAYLOAD_SIZE = 2048

PREFERRED_SENSOR_TYPES = [
    "temperature",
    "humidity",
    "pressure",
    "carbon_dioxide",
    "wind_speed",
    "precipitation",
    "battery",
    "illuminance",
    "pm25",
    "pm10",
    "aqi",
]

SENSOR_DEVICE_CLASSES = [
    "temperature",
    "humidity",
    "atmospheric_pressure",
    "carbon_dioxide",
    "wind_speed",
    "precipitation_intensity",
    "battery",
    "illuminance",
    "pm25",
    "pm10",
    "aqi",
    "volatile_organic_compounds",
    "nitrogen_dioxide",
    "nitrogen_monoxide",
    "nitrous_oxide",
    "ozone",
    "sulphur_dioxide",
]