"""Utilities for creating and managing sensor payloads."""

from __future__ import annotations

import json
import logging

_LOGGER = logging.getLogger(__name__)


def round_sensor_value(value, decimal_places=1):
    """Round sensor value to specified decimal places."""
    if value is None:
        return None

    try:
        float_value = float(value)
        rounded_value = round(float_value, decimal_places)

        if decimal_places == 0:
            return int(rounded_value)

        return rounded_value
    except (ValueError, TypeError):
        _LOGGER.debug("Could not round value '%s', returning original", value)
        return value


def create_entity_payload(
    state,
    sensor_type="additional",
    custom_name=None,
    include_id=False,
    decimal_places=1,
) -> dict:
    """Create a payload for a single sensor entity."""
    if not state:
        return None

    entity_parts = state.entity_id.split(".")
    if len(entity_parts) < 2:
        return None

    entity_name = entity_parts[1]
    friendly_name = state.attributes.get("friendly_name", "")

    rounded_value = round_sensor_value(state.state, decimal_places)

    payload = {
        "val": rounded_value,
        "type": sensor_type,
    }

    if include_id:
        payload["id"] = entity_name

    if "unit_of_measurement" in state.attributes:
        payload["u"] = state.attributes.get("unit_of_measurement")

    if custom_name and custom_name.strip():
        payload["n"] = custom_name.strip()
    elif friendly_name:
        clean_name = friendly_name
        for word in ["sensor", "Sensor", "Module", "module"]:
            clean_name = clean_name.replace(word, "").strip()
        payload["n"] = clean_name
    else:
        payload["n"] = entity_name.replace("_", " ").title()

    if "icon" in state.attributes:
        icon = state.attributes.get("icon")
        if icon:
            payload["i"] = icon
            _LOGGER.debug("Added icon '%s' for entity %s", icon, state.entity_id)

    if "battery_percent" in state.attributes:
        battery = state.attributes.get("battery_percent")
        if battery is not None and float(battery) < 25:
            payload["bat"] = round_sensor_value(battery, decimal_places)

    if "device_class" in state.attributes:
        payload["device_class"] = state.attributes.get("device_class")

    _LOGGER.debug(
        "Created payload for %s (%s): %s", state.entity_id, sensor_type, payload
    )
    return payload


def estimate_payload_size(payload):
    """Estimate the size of the payload in bytes."""
    return len(json.dumps(payload))
