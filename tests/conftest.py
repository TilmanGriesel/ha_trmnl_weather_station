"""Fixtures for testing."""
import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from custom_components.trmnl_weather_station.const import CONF_CO2_SENSOR, CONF_URL, DOMAIN


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Test TRMNL Weather Station",
        data={
            CONF_URL: "https://example.com/webhook",
            CONF_CO2_SENSOR: "sensor.test_co2",
        },
        options={},
        source="user",
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_hass(hass: HomeAssistant):
    """Return a mock Home Assistant instance."""
    return hass
