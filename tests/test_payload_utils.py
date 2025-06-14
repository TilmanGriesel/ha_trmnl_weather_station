"""Test payload utils."""
import pytest
from homeassistant.core import State

from custom_components.trmnl_weather_station.payload_utils import create_entity_payload, estimate_payload_size, round_sensor_value


def test_round_sensor_value():
    """Test round_sensor_value function."""
    assert round_sensor_value(None) is None
    assert round_sensor_value("invalid") == "invalid"
    assert round_sensor_value(1.0, 1) == 1
    assert round_sensor_value(1.23, 1) == 1.2
    assert round_sensor_value(1.56, 1) == 1.6
    assert round_sensor_value(1.5, 0) == 2


def test_create_entity_payload_basic():
    """Test basic entity payload creation."""
    state = State("sensor.test_sensor", "23.5", {"unit_of_measurement": "°C"})
    payload = create_entity_payload(state)

    assert payload["val"] == 23.5
    assert payload["type"] == "additional"
    assert payload["u"] == "°C"
    assert payload["n"] == "Test Sensor"


def test_create_entity_payload_with_custom_name():
    """Test entity payload with custom name."""
    state = State("sensor.test_sensor", "23.5", {"unit_of_measurement": "°C"})
    payload = create_entity_payload(state, custom_name="Custom Name")

    assert payload["n"] == "Custom Name"


def test_create_entity_payload_with_friendly_name():
    """Test entity payload with friendly name."""
    state = State(
        "sensor.test_sensor",
        "23.5",
        {"unit_of_measurement": "°C", "friendly_name": "Temperature Sensor"},
    )
    payload = create_entity_payload(state)

    assert payload["n"] == "Temperature"


def test_create_entity_payload_with_icon():
    """Test entity payload with icon."""
    state = State(
        "sensor.test_sensor",
        "23.5",
        {"unit_of_measurement": "°C", "icon": "mdi:thermometer"},
    )
    payload = create_entity_payload(state)

    assert payload["i"] == "mdi:thermometer"


def test_create_entity_payload_with_low_battery():
    """Test entity payload with low battery."""
    state = State(
        "sensor.test_sensor",
        "23.5",
        {"unit_of_measurement": "°C", "battery_percent": 20},
    )
    payload = create_entity_payload(state)

    assert payload["bat"] == 20


def test_create_entity_payload_with_device_class():
    """Test entity payload with device class."""
    state = State(
        "sensor.test_sensor",
        "23.5",
        {"unit_of_measurement": "°C", "device_class": "temperature"},
    )
    payload = create_entity_payload(state)

    assert payload["device_class"] == "temperature"


def test_create_entity_payload_with_include_id():
    """Test entity payload with ID included."""
    state = State("sensor.test_sensor", "23.5", {"unit_of_measurement": "°C"})
    payload = create_entity_payload(state, include_id=True)

    assert payload["id"] == "test_sensor"


def test_create_entity_payload_invalid_state():
    """Test entity payload with invalid state."""
    payload = create_entity_payload(None)
    assert payload is None


def test_estimate_payload_size():
    """Test payload size estimation."""
    payload = {"test": "data", "number": 123}
    size = estimate_payload_size(payload)
    assert isinstance(size, int)
    assert size > 0
