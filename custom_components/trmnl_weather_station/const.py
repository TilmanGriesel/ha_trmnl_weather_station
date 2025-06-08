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
CONF_DECIMAL_PLACES = "decimal_places"

DEFAULT_URL = ""
MIN_TIME_BETWEEN_UPDATES = 10
DEFAULT_UPDATE_INTERVAL = 10
DEFAULT_DECIMAL_PLACES = 1

MAX_PAYLOAD_SIZE = 2048

WEATHER_SENSOR_DEVICE_CLASSES = [
    "apparent_power",
    "aqi",
    "atmospheric_pressure",  # alias: pressure
    "carbon_dioxide",  # CO₂
    "carbon_monoxide",  # CO
    "conductivity",  # applicable in rain or soil sensors
    "humidity",
    "illuminance",
    "irradiance",
    "nitrogen_dioxide",
    "nitrogen_monoxide",
    "nitrous_oxide",
    "ozone",
    "pm1",
    "pm25",
    "pm10",
    "precipitation",
    "precipitation_intensity",
    "sound_pressure",  # ambient noise
    "speed",  # wind speed general
    "sulphur_dioxide",
    "temperature",
    "volatile_organic_compounds",
    "volatile_organic_compounds_parts",
    "wind_direction",
    "wind_speed",
]

OTHER_SENSOR_DEVICE_CLASSES = [
    "area",
    "battery",
    "blood_glucose_concentration",
    "current",
    "data_rate",
    "data_size",
    "date",
    "distance",
    "duration",
    "energy",
    "energy_distance",
    "energy_storage",
    "enum",
    "frequency",
    "gas",
    "moisture",
    "monetary",
    "power",
    "power_factor",
    "reactive_energy",
    "reactive_power",
    "signal_strength",
    "timestamp",
    "voltage",
    "volume",
    "volume_flow_rate",
    "volume_storage",
    "water",
    "weight",
]

SENSOR_DEVICE_CLASSES = WEATHER_SENSOR_DEVICE_CLASSES + OTHER_SENSOR_DEVICE_CLASSES
