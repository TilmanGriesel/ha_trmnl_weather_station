"""Test sensor processor."""
import pytest
from aioresponses import aioresponses
from homeassistant.core import HomeAssistant

from custom_components.trmnl_weather_station.sensor_processor import SensorProcessor


async def test_sensor_processor_success(hass: HomeAssistant, mock_config_entry):
    """Test successful sensor processing."""
    hass.states.async_set("sensor.test_co2", "400", {"unit_of_measurement": "ppm"})

    processor = SensorProcessor(hass, mock_config_entry)

    with aioresponses() as mock_http:
        mock_http.post(
            "https://example.com/webhook", status=200, payload={"success": True}
        )

        await processor.process_sensors()

        assert len(mock_http.requests) == 1
        request = mock_http.requests[("POST", "https://example.com/webhook")][0]
        payload = request.kwargs["json"]

        assert "merge_variables" in payload
        assert "entities" in payload["merge_variables"]
        assert len(payload["merge_variables"]["entities"]) == 1
        assert payload["merge_variables"]["entities"][0]["val"] == 400


async def test_sensor_processor_no_co2_sensor(hass: HomeAssistant, mock_config_entry):
    """Test sensor processing with missing CO2 sensor."""
    processor = SensorProcessor(hass, mock_config_entry)

    with aioresponses() as mock_http:
        await processor.process_sensors()

        assert len(mock_http.requests) == 0


async def test_sensor_processor_with_additional_sensors(
    hass: HomeAssistant, mock_config_entry
):
    """Test sensor processing with additional sensors."""
    hass.states.async_set("sensor.test_co2", "400", {"unit_of_measurement": "ppm"})
    hass.states.async_set("sensor.temperature", "23.5", {"unit_of_measurement": "°C"})

    mock_config_entry.data["sensor_1"] = "sensor.temperature"
    mock_config_entry.data["sensor_1_name"] = "Room Temperature"

    processor = SensorProcessor(hass, mock_config_entry)

    with aioresponses() as mock_http:
        mock_http.post(
            "https://example.com/webhook", status=200, payload={"success": True}
        )

        await processor.process_sensors()

        request = mock_http.requests[("POST", "https://example.com/webhook")][0]
        payload = request.kwargs["json"]

        assert len(payload["merge_variables"]["entities"]) == 2

        co2_entity = next(
            e for e in payload["merge_variables"]["entities"] if e.get("primary")
        )
        temp_entity = next(
            e for e in payload["merge_variables"]["entities"] if not e.get("primary")
        )

        assert co2_entity["val"] == 400
        assert temp_entity["val"] == 23.5
        assert temp_entity["n"] == "Room Temperature"


async def test_sensor_processor_http_error(hass: HomeAssistant, mock_config_entry):
    """Test sensor processing with HTTP error."""
    hass.states.async_set("sensor.test_co2", "400", {"unit_of_measurement": "ppm"})

    processor = SensorProcessor(hass, mock_config_entry)

    with aioresponses() as mock_http:
        mock_http.post(
            "https://example.com/webhook", status=500, payload={"error": "Server error"}
        )

        await processor.process_sensors()

        assert len(mock_http.requests) == 1
