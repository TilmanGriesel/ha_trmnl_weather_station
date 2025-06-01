"""The TRMNL Weather Station Push integration."""

from __future__ import annotations

import logging
import json
from datetime import datetime, timedelta
import asyncio
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    CONF_URL,
    CONF_CO2_SENSOR,
    CONF_CO2_NAME,
    CONF_SENSOR_1,
    CONF_SENSOR_1_NAME,
    CONF_SENSOR_2,
    CONF_SENSOR_2_NAME,
    CONF_SENSOR_3,
    CONF_SENSOR_3_NAME,
    CONF_SENSOR_4,
    CONF_SENSOR_4_NAME,
    MIN_TIME_BETWEEN_UPDATES,
    MAX_PAYLOAD_SIZE,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def create_entity_payload(state, sensor_type="additional", custom_name=None) -> dict:
    """Create a payload for a single sensor entity."""
    if not state:
        return None

    entity_parts = state.entity_id.split(".")
    if len(entity_parts) < 2:
        return None

    entity_name = entity_parts[1]
    friendly_name = state.attributes.get("friendly_name", "")

    # Basic payload
    payload = {
        "id": entity_name,
        "val": state.state,
        "type": sensor_type,
    }

    # Add unit if available
    if "unit_of_measurement" in state.attributes:
        payload["u"] = state.attributes.get("unit_of_measurement")

    # Use custom name if provided, otherwise clean up the friendly name
    if custom_name and custom_name.strip():
        payload["n"] = custom_name.strip()
    elif friendly_name:
        # Clean up the name - remove common prefixes/suffixes
        clean_name = friendly_name
        for word in ["sensor", "Sensor", "Module", "module"]:
            clean_name = clean_name.replace(word, "").strip()
        payload["n"] = clean_name
    else:
        payload["n"] = entity_name.replace("_", " ").title()

    # Add battery status if low
    if "battery_percent" in state.attributes:
        battery = state.attributes.get("battery_percent")
        if battery is not None and float(battery) < 25:
            payload["battery"] = battery

    # Add device class for better categorization
    if "device_class" in state.attributes:
        payload["device_class"] = state.attributes.get("device_class")

    _LOGGER.debug(
        "Created payload for %s (%s): %s", state.entity_id, sensor_type, payload
    )
    return payload


def estimate_payload_size(payload):
    """Estimate the size of the payload in bytes."""
    return len(json.dumps(payload))


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

        # Get configuration from both data and options (options take priority)
        config = {**entry.data, **entry.options}

        url = config.get(CONF_URL)
        co2_sensor = config.get(CONF_CO2_SENSOR)
        co2_name = config.get(CONF_CO2_NAME)
        sensor_1 = config.get(CONF_SENSOR_1)
        sensor_1_name = config.get(CONF_SENSOR_1_NAME)
        sensor_2 = config.get(CONF_SENSOR_2)
        sensor_2_name = config.get(CONF_SENSOR_2_NAME)
        sensor_3 = config.get(CONF_SENSOR_3)
        sensor_3_name = config.get(CONF_SENSOR_3_NAME)
        sensor_4 = config.get(CONF_SENSOR_4)
        sensor_4_name = config.get(CONF_SENSOR_4_NAME)
        update_interval = config.get("update_interval", MIN_TIME_BETWEEN_UPDATES)

        if not url:
            _LOGGER.error("No URL configured, cannot set up integration")
            return False

        if not co2_sensor:
            _LOGGER.error("No CO2 sensor configured, cannot set up integration")
            return False

        _LOGGER.debug(
            "Configuration - URL: %s, CO2: %s (%s), Sensors: [%s (%s), %s (%s), %s (%s), %s (%s)], Interval: %ds",
            url,
            co2_sensor,
            co2_name,
            sensor_1,
            sensor_1_name,
            sensor_2,
            sensor_2_name,
            sensor_3,
            sensor_3_name,
            sensor_4,
            sensor_4_name,
            update_interval,
        )

    except Exception as ex:
        _LOGGER.exception("Error setting up integration: %s", ex)
        return False

    async def process_sensors(*_):
        """Process and send sensor data to TRMNL."""
        _LOGGER.debug("Starting sensor data processing")

        # Get current configuration (in case it was updated)
        current_config = {**entry.data, **entry.options}
        current_url = current_config.get(CONF_URL)
        current_co2_sensor = current_config.get(CONF_CO2_SENSOR)
        current_co2_name = current_config.get(CONF_CO2_NAME)
        current_sensor_1 = current_config.get(CONF_SENSOR_1)
        current_sensor_1_name = current_config.get(CONF_SENSOR_1_NAME)
        current_sensor_2 = current_config.get(CONF_SENSOR_2)
        current_sensor_2_name = current_config.get(CONF_SENSOR_2_NAME)
        current_sensor_3 = current_config.get(CONF_SENSOR_3)
        current_sensor_3_name = current_config.get(CONF_SENSOR_3_NAME)
        current_sensor_4 = current_config.get(CONF_SENSOR_4)
        current_sensor_4_name = current_config.get(CONF_SENSOR_4_NAME)

        entities_payload = []

        # Get CO2 sensor (required - marked as primary)
        co2_state = hass.states.get(current_co2_sensor) if current_co2_sensor else None
        if co2_state:
            co2_payload = create_entity_payload(
                co2_state, sensor_type="co2_primary", custom_name=current_co2_name
            )
            if co2_payload:
                co2_payload["primary"] = True  # Mark CO2 as primary sensor
                entities_payload.append(co2_payload)
                _LOGGER.debug(
                    "Added CO2 sensor (primary): %s with name '%s'",
                    current_co2_sensor,
                    co2_payload.get("n"),
                )
        else:
            _LOGGER.warning("CO2 sensor %s not found", current_co2_sensor)
            return  # Don't send anything if CO2 sensor is missing

        # Get additional sensors (1-4)
        additional_sensors = [
            (current_sensor_1, current_sensor_1_name, "sensor_1"),
            (current_sensor_2, current_sensor_2_name, "sensor_2"),
            (current_sensor_3, current_sensor_3_name, "sensor_3"),
            (current_sensor_4, current_sensor_4_name, "sensor_4"),
        ]

        for sensor_id, custom_name, sensor_label in additional_sensors:
            if sensor_id:
                sensor_state = hass.states.get(sensor_id)
                if sensor_state:
                    sensor_payload = create_entity_payload(
                        sensor_state, sensor_type=sensor_label, custom_name=custom_name
                    )
                    if sensor_payload:
                        entities_payload.append(sensor_payload)
                        _LOGGER.debug(
                            "Added %s: %s with name '%s'",
                            sensor_label,
                            sensor_id,
                            sensor_payload.get("n"),
                        )
                else:
                    _LOGGER.warning("Sensor %s (%s) not found", sensor_label, sensor_id)

        if not entities_payload:
            _LOGGER.error("No valid sensor data to send")
            return

        # Create final payload
        timestamp = datetime.now().isoformat()
        payload = {
            "merge_variables": {
                "entities": entities_payload,
                "timestamp": timestamp,
                "count": len(entities_payload),
                "co2_value": co2_state.state if co2_state else None,
                "co2_unit": (
                    co2_state.attributes.get("unit_of_measurement", "ppm")
                    if co2_state
                    else "ppm"
                ),
            }
        }

        # Check payload size
        final_size = estimate_payload_size(payload)
        _LOGGER.debug(
            "Payload size: %d bytes (%d entities)", final_size, len(entities_payload)
        )

        if final_size > MAX_PAYLOAD_SIZE:
            _LOGGER.warning(
                "Payload exceeds 2KB limit (%d bytes). Trimming...", final_size
            )

            # Always keep CO2 sensor (primary)
            essential_payloads = [p for p in entities_payload if p.get("primary")]
            other_payloads = [p for p in entities_payload if not p.get("primary")]

            # Add back other sensors until we hit the limit
            final_payloads = essential_payloads.copy()
            for sensor_payload in other_payloads:
                test_payload = {
                    "merge_variables": {
                        "entities": final_payloads + [sensor_payload],
                        "timestamp": timestamp,
                        "count": len(final_payloads) + 1,
                        "co2_value": co2_state.state if co2_state else None,
                        "co2_unit": (
                            co2_state.attributes.get("unit_of_measurement", "ppm")
                            if co2_state
                            else "ppm"
                        ),
                    }
                }
                if estimate_payload_size(test_payload) <= MAX_PAYLOAD_SIZE:
                    final_payloads.append(sensor_payload)
                else:
                    break

            payload["merge_variables"]["entities"] = final_payloads
            payload["merge_variables"]["count"] = len(final_payloads)
            final_size = estimate_payload_size(payload)
            _LOGGER.debug(
                "Trimmed payload size: %d bytes (%d entities)",
                final_size,
                len(final_payloads),
            )

        # Send to TRMNL
        try:
            async with aiohttp.ClientSession() as session:
                _LOGGER.debug("Sending data to TRMNL webhook")
                async with session.post(current_url, json=payload) as response:
                    if response.status == 200:
                        _LOGGER.info(
                            "Successfully sent %d sensors to TRMNL (CO2: %s)",
                            len(entities_payload),
                            co2_state.state if co2_state else "unknown",
                        )
                        _LOGGER.debug("Response: %s", await response.text())
                    else:
                        _LOGGER.error("Webhook error: %s", response.status)
                        _LOGGER.error("Response: %s", await response.text())
        except Exception as err:
            _LOGGER.error("Failed to send data to webhook: %s", err)

    # Set up periodic updates
    _LOGGER.debug("Setting up periodic timer for %d seconds", update_interval)
    remove_timer = async_track_time_interval(
        hass, process_sensors, timedelta(seconds=update_interval)
    )

    # Store the timer removal function
    hass.data[DOMAIN][entry.entry_id]["remove_timer"] = remove_timer

    # Set up entry update listener for options changes
    async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Update listener to handle option changes."""
        _LOGGER.debug("Configuration updated, reloading integration")
        await hass.config_entries.async_reload(entry.entry_id)

    entry.add_update_listener(async_update_entry)

    # Run initial update
    _LOGGER.debug("Running initial sensor update")
    await process_sensors()

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
