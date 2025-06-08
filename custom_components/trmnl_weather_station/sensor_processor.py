"""Sensor data processing and webhook communication."""

from __future__ import annotations

import logging
from datetime import datetime
import asyncio
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
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
    CONF_SENSOR_5,
    CONF_SENSOR_5_NAME,
    CONF_SENSOR_6,
    CONF_SENSOR_6_NAME,
    CONF_INCLUDE_IDS,
    CONF_DECIMAL_PLACES,
    DEFAULT_DECIMAL_PLACES,
    MAX_PAYLOAD_SIZE,
)
from .payload_utils import create_entity_payload, estimate_payload_size, round_sensor_value

_LOGGER = logging.getLogger(__name__)


class SensorProcessor:
    """Handle sensor data processing and webhook communication."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the sensor processor."""
        self.hass = hass
        self.entry = entry

    async def process_sensors(self, *_):
        """Process and send sensor data to TRMNL."""
        _LOGGER.debug("Starting sensor data processing")

        current_config = {**self.entry.data, **self.entry.options}
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
        current_sensor_5 = current_config.get(CONF_SENSOR_5)
        current_sensor_5_name = current_config.get(CONF_SENSOR_5_NAME)
        current_sensor_6 = current_config.get(CONF_SENSOR_6)
        current_sensor_6_name = current_config.get(CONF_SENSOR_6_NAME)
        include_ids = current_config.get(CONF_INCLUDE_IDS, False)
        decimal_places = current_config.get(CONF_DECIMAL_PLACES, DEFAULT_DECIMAL_PLACES)

        _LOGGER.debug("Using %d decimal places for sensor values", decimal_places)

        entities_payload = []

        co2_state = self.hass.states.get(current_co2_sensor) if current_co2_sensor else None
        if co2_state:
            co2_payload = create_entity_payload(
                co2_state, 
                sensor_type="co2_primary", 
                custom_name=current_co2_name,
                include_id=include_ids,
                decimal_places=decimal_places
            )
            if co2_payload:
                co2_payload["primary"] = True
                entities_payload.append(co2_payload)
                _LOGGER.debug(
                    "Added CO2 sensor (primary): %s with name '%s' and value %s",
                    current_co2_sensor,
                    co2_payload.get("n"),
                    co2_payload.get("val"),
                )
        else:
            _LOGGER.warning("CO2 sensor %s not found", current_co2_sensor)
            return

        additional_sensors = [
            (current_sensor_1, current_sensor_1_name, "sensor_1"),
            (current_sensor_2, current_sensor_2_name, "sensor_2"),
            (current_sensor_3, current_sensor_3_name, "sensor_3"),
            (current_sensor_4, current_sensor_4_name, "sensor_4"),
            (current_sensor_5, current_sensor_5_name, "sensor_5"),
            (current_sensor_6, current_sensor_6_name, "sensor_6"),
        ]

        for sensor_id, custom_name, sensor_label in additional_sensors:
            if sensor_id and isinstance(sensor_id, str) and sensor_id.strip():
                sensor_state = self.hass.states.get(sensor_id.strip())
                if sensor_state:
                    sensor_payload = create_entity_payload(
                        sensor_state, 
                        sensor_type=sensor_label, 
                        custom_name=custom_name,
                        include_id=include_ids,
                        decimal_places=decimal_places
                    )
                    if sensor_payload:
                        entities_payload.append(sensor_payload)
                        _LOGGER.debug(
                            "Added %s: %s with name '%s' and value %s",
                            sensor_label,
                            sensor_id,
                            sensor_payload.get("n"),
                            sensor_payload.get("val"),
                        )
                else:
                    _LOGGER.warning("Sensor %s (%s) not found", sensor_label, sensor_id)

        if not entities_payload:
            _LOGGER.error("No valid sensor data to send")
            return

        timestamp = datetime.now().isoformat()

        rounded_co2_value = round_sensor_value(co2_state.state, decimal_places) if co2_state else None
        
        payload = {
            "merge_variables": {
                "entities": entities_payload,
                "timestamp": timestamp,
                "count": len(entities_payload),
                "co2_value": rounded_co2_value,
                "co2_unit": (
                    co2_state.attributes.get("unit_of_measurement", "ppm")
                    if co2_state
                    else "ppm"
                ),
            }
        }

        final_size = estimate_payload_size(payload)
        _LOGGER.debug(
            "Payload size: %d bytes (%d entities)", final_size, len(entities_payload)
        )

        if final_size > MAX_PAYLOAD_SIZE:
            _LOGGER.warning(
                "Payload exceeds 2KB limit (%d bytes). Trimming...", final_size
            )

            essential_payloads = [p for p in entities_payload if p.get("primary")]
            other_payloads = [p for p in entities_payload if not p.get("primary")]

            final_payloads = essential_payloads.copy()
            for sensor_payload in other_payloads:
                test_payload = {
                    "merge_variables": {
                        "entities": final_payloads + [sensor_payload],
                        "timestamp": timestamp,
                        "count": len(final_payloads) + 1,
                        "co2_value": rounded_co2_value,
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

        try:
            async with aiohttp.ClientSession() as session:
                _LOGGER.debug("Sending data to TRMNL webhook")
                async with session.post(current_url, json=payload) as response:
                    if response.status == 200:
                        _LOGGER.info(
                            "Successfully sent %d sensors to TRMNL (CO2: %s)",
                            len(entities_payload),
                            rounded_co2_value,
                        )
                        _LOGGER.debug("Response: %s", await response.text())
                    else:
                        _LOGGER.error("Webhook error: %s", response.status)
                        _LOGGER.error("Response: %s", await response.text())
        except Exception as err:
            _LOGGER.error("Failed to send data to webhook: %s", err)