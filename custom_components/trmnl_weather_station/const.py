"""Constants for the TRMNL Weather Station Push integration."""

DOMAIN = "trmnl_weather_station"
CONF_URL = "url"
CONF_CO2_SENSOR = "co2_sensor"  # Required CO2 sensor
CONF_CO2_NAME = "co2_name"  # Custom name for CO2 sensor
CONF_SENSOR_1 = "sensor_1"
CONF_SENSOR_1_NAME = "sensor_1_name"  # Custom name for sensor 1
CONF_SENSOR_2 = "sensor_2"
CONF_SENSOR_2_NAME = "sensor_2_name"  # Custom name for sensor 2
CONF_SENSOR_3 = "sensor_3"
CONF_SENSOR_3_NAME = "sensor_3_name"  # Custom name for sensor 3
CONF_SENSOR_4 = "sensor_4"
CONF_SENSOR_4_NAME = "sensor_4_name"  # Custom name for sensor 4

DEFAULT_URL = "https://usetrmnl.com/api/custom_plugins/XXXX-XXXX-XXXX-XXXX"
MIN_TIME_BETWEEN_UPDATES = 1800  # 30 minutes

# API limit for TRMNL
MAX_PAYLOAD_SIZE = 2048  # 2KB max payload size

# Preferred sensor types for quick selection
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

# Device classes for sensor filtering
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
