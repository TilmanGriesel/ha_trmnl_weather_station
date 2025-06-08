"""Utilities for creating and managing sensor payloads."""

from __future__ import annotations

import json
import logging

_LOGGER = logging.getLogger(__name__)


def create_entity_payload(state, sensor_type="additional", custom_name=None, include_id=False) -> dict:
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
        "val": state.state,
        "type": sensor_type,
    }

    # Conditionally include entity ID
    if include_id:
        payload["id"] = entity_name

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