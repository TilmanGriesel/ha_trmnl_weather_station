"""Test the TRMNL Weather Station integration setup."""
import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.trmnl_weather_station import async_setup, async_setup_entry, async_unload_entry
from custom_components.trmnl_weather_station.const import DOMAIN


async def test_async_setup(hass: HomeAssistant):
    """Test the component setup."""
    result = await async_setup(hass, {})
    assert result is True


async def test_async_setup_entry_success(hass: HomeAssistant, mock_config_entry):
    """Test successful setup entry."""
    hass.states.async_set("sensor.test_co2", "400", {"unit_of_measurement": "ppm"})

    result = await async_setup_entry(hass, mock_config_entry)
    assert result is True
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_async_setup_entry_no_url(hass: HomeAssistant, mock_config_entry):
    """Test setup entry fails without URL."""
    mock_config_entry.data.pop("url")

    result = await async_setup_entry(hass, mock_config_entry)
    assert result is False


async def test_async_setup_entry_no_co2_sensor(hass: HomeAssistant, mock_config_entry):
    """Test setup entry fails without CO2 sensor."""
    mock_config_entry.data.pop("co2_sensor")

    result = await async_setup_entry(hass, mock_config_entry)
    assert result is False


async def test_async_unload_entry(hass: HomeAssistant, mock_config_entry):
    """Test unloading entry."""
    hass.states.async_set("sensor.test_co2", "400", {"unit_of_measurement": "ppm"})

    await async_setup_entry(hass, mock_config_entry)
    result = await async_unload_entry(hass, mock_config_entry)

    assert result is True
    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})
