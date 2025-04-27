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
    MIN_TIME_BETWEEN_UPDATES,
    DEFAULT_WEATHER_DOMAINS,
    PRIORITY_SENSORS,
    TOP_PRIORITY_SENSORS,
    MAX_PAYLOAD_SIZE,
    CONF_STATION_KEYWORD,
    DEFAULT_STATION_KEYWORD,
    CONF_PRIMARY_CO2,
    CONF_DEVICES,
    CONF_INCLUDE_OUTDOOR,
    OUTDOOR_KEYWORDS,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def create_compact_entity_payload(state) -> dict:
    """Create a compact payload for a single weather entity."""
    # Extract the sensor type
    entity_parts = state.entity_id.split(".")
    if len(entity_parts) < 2:
        return None

    entity_name = entity_parts[1]

    # Basic payload with minimal data
    payload = {
        "id": entity_name,
        "val": state.state,
    }

    # Add unit if available (using short key)
    if "unit_of_measurement" in state.attributes:
        payload["u"] = state.attributes.get("unit_of_measurement")

    # Add human-readable name (if different from entity_id)
    if "friendly_name" in state.attributes:
        friendly_name = state.attributes.get("friendly_name")
        if friendly_name and friendly_name != entity_name:
            # Only include abbreviated module name to save space
            if "module_name" in state.attributes:
                module_name = state.attributes.get("module_name")
                # Just use the first word of the module name to save some space
                if module_name and " " in module_name:
                    payload["m"] = module_name.split(" ")[0]
                else:
                    payload["m"] = module_name
            else:
                # Use friendly name if no module name
                payload["m"] = friendly_name

    # Add battery only if it's low (<25%)
    if "battery_percent" in state.attributes:
        battery = state.attributes.get("battery_percent")
        if battery is not None and float(battery) < 25:
            payload["bat"] = battery

    # Skip signal strength to save space unless critical
    if "rf_status" in state.attributes:
        rf_status = state.attributes.get("rf_status")
        if rf_status is not None and float(rf_status) < 30:
            payload["sig"] = rf_status

    _LOGGER.debug(
        "TRMNL Weather: Created compact payload for %s: %s", state.entity_id, payload
    )
    return payload


def estimate_payload_size(payload):
    """Estimate the size of the payload in bytes."""
    return len(json.dumps(payload))


def is_priority_sensor(entity_id):
    """Check if an entity represents a priority sensor type."""
    # Check top priority sensors first (CO2, Temperature, Humidity)
    for i, sensor_type in enumerate(TOP_PRIORITY_SENSORS):
        if sensor_type in entity_id:
            return True, i

    # Then check the rest of priority sensors
    for i, sensor_type in enumerate(
        PRIORITY_SENSORS[len(TOP_PRIORITY_SENSORS) :], len(TOP_PRIORITY_SENSORS)
    ):
        if sensor_type in entity_id:
            return True, i

    return False, len(PRIORITY_SENSORS)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    _LOGGER.debug("TRMNL Weather: Setting up TRMNL Weather Push component")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("TRMNL Weather: Setting up config entry")

    try:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {}

        # Get configuration values with defaults
        url = entry.data.get(CONF_URL)
        if not url:
            _LOGGER.error("TRMNL Weather: No URL configured, cannot set up integration")
            return False

        station_keyword = entry.data.get(CONF_STATION_KEYWORD, DEFAULT_STATION_KEYWORD)
        selected_devices = entry.data.get(CONF_DEVICES, [])
        include_outdoor = entry.data.get(CONF_INCLUDE_OUTDOOR, True)
        primary_co2_filter = entry.data.get(
            CONF_PRIMARY_CO2, ""
        ).strip()  # TODO: Remove primary_co2_filter

        _LOGGER.debug(
            "TRMNL Weather: Using webhook URL: %s, station keyword: %s, "
            "selected devices: %s, include outdoor: %s, primary CO2 filter: %s",
            url,
            station_keyword,
            selected_devices,
            include_outdoor,
            primary_co2_filter,
        )

    except Exception as ex:
        _LOGGER.exception("TRMNL Weather: Error setting up integration: %s", ex)
        return False

    def get_weather_station_entities():
        """Get all Weather Station entities prioritized by importance."""
        _LOGGER.debug("TRMNL Weather: Finding Weather Station entities")
        all_entities = []

        domains_to_check = DEFAULT_WEATHER_DOMAINS.copy()
        if station_keyword and station_keyword not in domains_to_check:
            domains_to_check.append(station_keyword)

        entity_registry = async_get_entity_registry(hass)
        device_registry = dr.async_get(hass)

        _LOGGER.debug("TRMNL Weather: Selected devices: %s", selected_devices)

        for entity_id in hass.states.async_entity_ids():
            if any(domain in entity_id for domain in domains_to_check):
                state = hass.states.get(entity_id)
                if state:
                    if entity_id.startswith(("sensor.", "binary_sensor.")):
                        entity_entry = entity_registry.async_get(entity_id)

                        should_include = False

                        _LOGGER.debug(
                            "TRMNL Weather: Processing entity %s for device matching",
                            entity_id,
                        )

                        if entity_entry and entity_entry.device_id:
                            _LOGGER.debug(
                                "TRMNL Weather: Entity %s has device_id: %s (selected devices: %s)",
                                entity_id,
                                entity_entry.device_id,
                                selected_devices,
                            )

                            if not selected_devices:
                                should_include = True
                                _LOGGER.debug(
                                    "TRMNL Weather: OK - Including %s - no specific devices selected",
                                    entity_id,
                                )
                            elif entity_entry.device_id in selected_devices:
                                should_include = True

                                device = device_registry.async_get(
                                    entity_entry.device_id
                                )
                                device_name = (
                                    device.name if device else "Unknown device"
                                )

                                _LOGGER.debug(
                                    "TRMNL Weather: OK - Including %s - matched with selected device %s (%s)",
                                    entity_id,
                                    entity_entry.device_id,
                                    device_name,
                                )
                            else:
                                _LOGGER.debug(
                                    "TRMNL Weather: NOOP - Not including %s - device %s not in selected devices",
                                    entity_id,
                                    entity_entry.device_id,
                                )
                        else:
                            if entity_entry:
                                _LOGGER.debug(
                                    "TRMNL Weather: Entity %s has no device_id assigned",
                                    entity_id,
                                )
                            else:
                                _LOGGER.debug(
                                    "TRMNL Weather: Entity %s not found in entity registry",
                                    entity_id,
                                )

                        if not selected_devices and not should_include:
                            should_include = True
                            _LOGGER.debug(
                                "TRMNL Weather: No devices are selected. Including entity %s by default.",
                                entity_id,
                            )

                        # If user wants to always include outdoor devices
                        if include_outdoor and not should_include:
                            entity_name = entity_id.lower()
                            friendly_name = state.attributes.get(
                                "friendly_name", ""
                            ).lower()

                            for keyword in OUTDOOR_KEYWORDS:
                                if keyword in entity_name or keyword in friendly_name:
                                    should_include = True
                                    _LOGGER.debug(
                                        "TRMNL Weather: OK - Including outdoor sensor %s (matched keyword: %s)",
                                        entity_id,
                                        keyword,
                                    )
                                    break

                            if not should_include:
                                _LOGGER.debug(
                                    "TRMNL Weather: NOOP - Not including %s - not matching any outdoor keywords",
                                    entity_id,
                                )

                        # Include entity if it passed filters
                        if should_include:
                            all_entities.append(entity_id)
                        else:
                            _LOGGER.debug(
                                "TRMNL Weather: NOOP - Not including %s - did not pass any inclusion filters",
                                entity_id,
                            )

        # Ensure TOP_PRIORITY_SENSORS come first
        def enhanced_priority_sort_key(entity_id):
            state = hass.states.get(entity_id)

            # First check for primary CO2 filter
            if (
                primary_co2_filter
                and TOP_PRIORITY_SENSORS[0] in entity_id
                and primary_co2_filter.lower() in entity_id.lower()
            ):  # TODO: Remove primary_co2_filter
                return (-1, entity_id)

            for i, sensor_type in enumerate(TOP_PRIORITY_SENSORS):
                if sensor_type in entity_id:
                    return (i, entity_id)

            is_priority, priority_idx = is_priority_sensor(entity_id)
            if is_priority:
                return (priority_idx, entity_id)
            else:
                return (999, entity_id)  # Non-priority sensors last

        all_entities.sort(key=enhanced_priority_sort_key)

        _LOGGER.debug(
            "TRMNL Weather: Found entities in priority order: %s", all_entities
        )
        return all_entities

    async def process_weather_station_entities(*_):
        """Process Weather Station entities efficiently."""
        _LOGGER.debug("TRMNL Weather: Starting entity processing")

        weather_entities = get_weather_station_entities()
        if len(weather_entities) == 0:
            _LOGGER.error("TRMNL Weather: No Weather Station entities found")
            return

        _LOGGER.info(
            "TRMNL Weather: Found %d Weather Station entities", len(weather_entities)
        )

        entities_payload = []
        included_count = 0
        current_size = 0

        included_types = {sensor_type: 0 for sensor_type in TOP_PRIORITY_SENSORS}
        included_types["other"] = 0

        base_payload_size = estimate_payload_size(
            {
                "merge_variables": {
                    "entities": [],
                    "timestamp": datetime.now().isoformat(),
                    "source": station_keyword,
                }
            }
        )

        available_size = (
            MAX_PAYLOAD_SIZE - base_payload_size - 100
        )  # 100 bytes buffer for base payload

        for entity_id in weather_entities:

            state = hass.states.get(entity_id)
            if state:
                _LOGGER.debug("TRMNL Weather: Processing entity: %s", entity_id)
                entity_payload = create_compact_entity_payload(state)

                if entity_payload:
                    entity_size = estimate_payload_size(entity_payload)
                    if current_size + entity_size <= available_size:
                        entities_payload.append(entity_payload)
                        current_size += entity_size
                        included_count += 1

                        # Track included sensor types
                        sensor_matched = False
                        for sensor_type in TOP_PRIORITY_SENSORS:
                            if sensor_type in entity_id:
                                included_types[sensor_type] += 1
                                sensor_matched = True

                                # Add special flag for primary CO2 sensor # TODO: Remove primary_co2_filter
                                if (
                                    sensor_type == TOP_PRIORITY_SENSORS[0]
                                    and primary_co2_filter
                                    and primary_co2_filter.lower() in entity_id.lower()
                                ):
                                    entity_payload["primary"] = True
                                break

                        if not sensor_matched:
                            included_types["other"] += 1

                        _LOGGER.debug(
                            "TRMNL Weather: Added entity (size: %d bytes, total: %d bytes)",
                            entity_size,
                            current_size,
                        )
                    else:
                        _LOGGER.debug(
                            "TRMNL Weather: Skipping entity %s - would exceed size limit",
                            entity_id,
                        )

        _LOGGER.info(
            "TRMNL Weather: Included %d out of %d entities (payload size: ~%d bytes)",
            included_count,
            len(weather_entities),
            current_size + base_payload_size,
        )

        log_parts = ["TRMNL Weather: Sensor type breakdown -"]
        for sensor_type in TOP_PRIORITY_SENSORS:
            formatted_name = sensor_type.replace("_", " ").capitalize()
            log_parts.append(f"{formatted_name}: {included_types[sensor_type]}")
        log_parts.append(f"Other: {included_types['other']}")

        _LOGGER.info(" ".join(log_parts))

        # Send to TRMNL webhook (if we have entities)
        if entities_payload:
            timestamp = datetime.now().isoformat()
            payload = {
                "merge_variables": {
                    "entities": entities_payload,
                    "timestamp": timestamp,
                    "source": station_keyword,
                    "count": included_count,
                }
            }

            # Add device information if devices are selected
            if selected_devices:
                device_reg = dr.async_get(hass)
                device_names = []

                for device_id in selected_devices:
                    device = device_reg.async_get(device_id)
                    if device and device.name:
                        device_names.append(device.name)

                if device_names:
                    payload["merge_variables"]["devices"] = device_names

            final_size = estimate_payload_size(payload)
            _LOGGER.debug("TRMNL Weather: Final payload size: %d bytes", final_size)

            if final_size > MAX_PAYLOAD_SIZE:
                _LOGGER.error(
                    "TRMNL Weather: Payload exceeds 2KB limit (%d bytes). Trimming payload.",
                    final_size,
                )
                # Remove entities until under the size limit
                while final_size > MAX_PAYLOAD_SIZE and entities_payload:
                    entities_payload.pop()
                    payload["merge_variables"]["entities"] = entities_payload
                    payload["merge_variables"]["count"] = len(entities_payload)
                    final_size = estimate_payload_size(payload)

                _LOGGER.debug(
                    "TRMNL Weather: Trimmed payload size: %d bytes with %d entities",
                    final_size,
                    len(entities_payload),
                )

            try:
                async with aiohttp.ClientSession() as session:
                    _LOGGER.debug("TRMNL Weather: Sending POST request to %s", url)
                    async with session.post(url, json=payload) as response:
                        if response.status == 200:
                            _LOGGER.info(
                                "TRMNL Weather: Successfully sent data to webhook"
                            )
                            _LOGGER.debug(
                                "TRMNL Weather: Webhook response: %s",
                                await response.text(),
                            )
                        else:
                            _LOGGER.error(
                                "TRMNL Weather: Error sending to webhook: %s",
                                response.status,
                            )
                            response_text = await response.text()
                            _LOGGER.error("TRMNL Weather: Response: %s", response_text)
            except Exception as err:
                _LOGGER.error("TRMNL Weather: Failed to send data to webhook: %s", err)
        else:
            _LOGGER.debug("TRMNL Weather: No entities to send")

    update_interval = entry.data.get("update_interval", MIN_TIME_BETWEEN_UPDATES)

    # Timer config
    _LOGGER.debug(
        "TRMNL Weather: Setting up periodic timer for %d seconds", update_interval
    )
    remove_timer = async_track_time_interval(
        hass, process_weather_station_entities, timedelta(seconds=update_interval)
    )

    # Store the timer removal function
    hass.data[DOMAIN][entry.entry_id]["remove_timer"] = remove_timer

    # Run initial scan
    _LOGGER.debug("TRMNL Weather: Running initial entity scan")
    await process_weather_station_entities()

    _LOGGER.info("TRMNL Weather: Integration setup completed for URL: %s", url)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        if entry.entry_id in hass.data[DOMAIN]:
            _LOGGER.debug("TRMNL Weather: Removing timer and cleaning up")
            hass.data[DOMAIN][entry.entry_id]["remove_timer"]()
            hass.data[DOMAIN].pop(entry.entry_id)
            _LOGGER.info("TRMNL Weather: Successfully unloaded integration")
    except Exception as err:
        _LOGGER.error("TRMNL Weather: Error unloading integration: %s", err)
        return False
    return True
