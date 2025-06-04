"""The TRMNL Weather Station Push integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, CONF_URL, CONF_CO2_SENSOR, MIN_TIME_BETWEEN_UPDATES
from .sensor_processor import SensorProcessor

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the TRMNL Weather component."""
    _LOGGER.debug("Setting up TRMNL Weather Push component")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TRMNL Weather from a config entry."""
    _LOGGER.debug("Setting up TRMNL Weather config entry")

    try:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {}

        config = {**entry.data, **entry.options}

        url = config.get(CONF_URL)
        co2_sensor = config.get(CONF_CO2_SENSOR)
        update_interval = config.get("update_interval", MIN_TIME_BETWEEN_UPDATES)

        if not url:
            _LOGGER.error("No URL configured, cannot set up integration")
            return False

        if not co2_sensor:
            _LOGGER.error("No CO2 sensor configured, cannot set up integration")
            return False

        _LOGGER.debug(
            "Configuration - URL: %s, CO2: %s, Interval: %ds",
            url,
            co2_sensor,
            update_interval,
        )

    except Exception as ex:
        _LOGGER.exception("Error setting up integration: %s", ex)
        return False

    # Create sensor processor instance
    processor = SensorProcessor(hass, entry)

    # Set up periodic updates
    _LOGGER.debug("Setting up periodic timer for %d seconds", update_interval)
    remove_timer = async_track_time_interval(
        hass, processor.process_sensors, timedelta(seconds=update_interval)
    )

    # Store the timer removal function and processor
    hass.data[DOMAIN][entry.entry_id]["remove_timer"] = remove_timer
    hass.data[DOMAIN][entry.entry_id]["processor"] = processor

    # Set up entry update listener for options changes
    async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Update listener to handle option changes."""
        _LOGGER.debug("Configuration updated, reloading integration")
        await hass.config_entries.async_reload(entry.entry_id)

    entry.add_update_listener(async_update_entry)

    # Run initial update
    _LOGGER.debug("Running initial sensor update")
    await processor.process_sensors()

    _LOGGER.info("TRMNL Weather integration setup completed")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        if entry.entry_id in hass.data[DOMAIN]:
            _LOGGER.debug("Removing timer and cleaning up")

            # Remove the timer
            if "remove_timer" in hass.data[DOMAIN][entry.entry_id]:
                hass.data[DOMAIN][entry.entry_id]["remove_timer"]()

            # Clean up data
            hass.data[DOMAIN].pop(entry.entry_id)
            _LOGGER.info("Successfully unloaded integration")
    except Exception as err:
        _LOGGER.error("Error unloading integration: %s", err)
        return False
    return True