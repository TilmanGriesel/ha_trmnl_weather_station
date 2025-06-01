"""Config flow for TRMNL Weather Station integration."""

from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from homeassistant.helpers.selector import (
    DeviceSelector,
    DeviceSelectorConfig,
    BooleanSelector,
)

has_device_selector = True

from .const import (
    DOMAIN,
    CONF_URL,
    MIN_TIME_BETWEEN_UPDATES,
    PRIORITY_SENSORS,
    TOP_PRIORITY_SENSORS,
    CONF_STATION_KEYWORD,
    DEFAULT_STATION_KEYWORD,
    CONF_PRIMARY_CO2,
    CONF_DEVICES,
    CONF_INCLUDE_OUTDOOR,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, str]:
    """Validate the user input allows us to connect."""
    # URL validation
    if not data[CONF_URL].startswith(("http://", "https://")):
        raise InvalidURL

    title_parts = ["TRMNL Weather Station"]

    if data.get(CONF_STATION_KEYWORD) != DEFAULT_STATION_KEYWORD:
        title_parts.append(data[CONF_STATION_KEYWORD].capitalize())

    # Add selected devices to title (if any)
    device_reg = dr.async_get(hass)
    selected_device_names = []
    for device_id in data.get(CONF_DEVICES, []):
        device = device_reg.async_get(device_id)
        if device and device.name:
            selected_device_names.append(device.name)

    if selected_device_names:
        title_parts.append(f"({', '.join(selected_device_names)})")
    else:
        # Add sensor types to title if no devices specified
        sensor_names = [
            s.replace("_", " ").capitalize() for s in TOP_PRIORITY_SENSORS[:2]
        ]
        title_parts.append(f"({', '.join(sensor_names)})")

    return {"title": " ".join(title_parts)}


class TrmnlWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TRMNL Weather."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except InvalidURL:
                errors["base"] = "invalid_url"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during config flow: %s", ex)
                errors["base"] = "unknown"

        # Device selector
        schema = vol.Schema(
            {
                vol.Required(CONF_URL): str,
                vol.Optional(
                    CONF_STATION_KEYWORD, default=DEFAULT_STATION_KEYWORD
                ): str,
                vol.Optional(CONF_DEVICES, default=[]): DeviceSelector(
                    DeviceSelectorConfig(
                        multiple=False,
                    )
                ),
                vol.Optional(CONF_INCLUDE_OUTDOOR, default=True): BooleanSelector(),
                vol.Optional(
                    "update_interval", default=MIN_TIME_BETWEEN_UPDATES
                ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400)),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "min_interval": "5 minutes",
                "max_interval": "24 hours",
                "priority_sensors": ", ".join(
                    [s.replace("_", " ").capitalize() for s in TOP_PRIORITY_SENSORS]
                ),
                "default_station": DEFAULT_STATION_KEYWORD,
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidURL(HomeAssistantError):
    """Error to indicate the URL is invalid."""
