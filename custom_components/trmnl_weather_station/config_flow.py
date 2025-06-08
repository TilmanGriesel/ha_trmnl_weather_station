"""Config flow for TRMNL Weather Station integration with multi-step approach."""

from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er

from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
)

from .const import (
    DOMAIN,
    CONF_URL,
    MIN_TIME_BETWEEN_UPDATES,
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
    DEFAULT_URL,
    SENSOR_DEVICE_CLASSES,
)

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================


def get_entity_selectors() -> tuple[dict, dict]:
    """Create entity selectors for CO2 and general sensors.

    Returns:
        tuple: (co2_filter, sensor_filter) dictionaries for entity selection
    """
    co2_filter = {
        "domain": ["sensor"],
        "device_class": ["carbon_dioxide"],
    }

    sensor_filter = {
        "domain": ["sensor"],
        "device_class": SENSOR_DEVICE_CLASSES,
    }

    return co2_filter, sensor_filter


def get_sensor_friendly_name(hass: HomeAssistant, entity_id: str) -> str:
    """Get a friendly name for a sensor entity.

    Args:
        hass: Home Assistant instance
        entity_id: The entity ID to get the name for

    Returns:
        str: A user-friendly name for the sensor
    """
    entity_registry = er.async_get(hass)
    entity = entity_registry.async_get(entity_id)

    if entity and entity.original_name:
        return entity.original_name

    # Fallback to parsing entity_id
    sensor_name = entity_id.split(".")[-1].replace("_", " ").title()
    return sensor_name


def clean_sensor_data(data: dict) -> dict:
    """Clean up sensor data by converting empty strings to None."""
    cleaned = data.copy()
    
    sensor_keys = [CONF_SENSOR_1, CONF_SENSOR_2, CONF_SENSOR_3, 
                   CONF_SENSOR_4, CONF_SENSOR_5, CONF_SENSOR_6]
    
    for key in sensor_keys:
        if key in cleaned:
            value = cleaned[key]
            # Convert empty strings, whitespace-only strings, or the string "None" to None
            if not value or (isinstance(value, str) and (not value.strip() or value.strip() == "None")):
                cleaned[key] = None
    
    return cleaned


def create_basic_schema(defaults: dict = None) -> vol.Schema:
    """Create the basic configuration schema for step 1.

    Args:
        defaults: Dictionary of default values for the form fields

    Returns:
        vol.Schema: The basic configuration schema
    """
    if defaults is None:
        defaults = {}

    co2_filter, _ = get_entity_selectors()

    schema_dict = {
        vol.Required(CONF_URL, default=defaults.get(CONF_URL, DEFAULT_URL)): str,
        vol.Required(
            CONF_CO2_SENSOR, default=defaults.get(CONF_CO2_SENSOR)
        ): EntitySelector(EntitySelectorConfig(filter=co2_filter)),
        vol.Optional(CONF_CO2_NAME, default=defaults.get(CONF_CO2_NAME, "CO2")): str,
        vol.Optional(
            "update_interval",
            default=defaults.get("update_interval", MIN_TIME_BETWEEN_UPDATES),
        ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400)),
    }

    return vol.Schema(schema_dict)


def create_sensors_schema(defaults: dict = None) -> vol.Schema:
    """Create the additional sensors schema for step 2.

    Args:
        defaults: Dictionary of default values for the form fields

    Returns:
        vol.Schema: The sensors configuration schema
    """
    if defaults is None:
        defaults = {}

    _, sensor_filter = get_entity_selectors()

    # Create EntitySelector that allows empty selection
    sensor_selector = EntitySelector(EntitySelectorConfig(
        filter=sensor_filter,
        multiple=False,
    ))

    schema_dict = {}
    
    # Add sensor fields, only setting defaults if they have actual values
    sensor_configs = [
        (CONF_SENSOR_1, CONF_SENSOR_1_NAME),
        (CONF_SENSOR_2, CONF_SENSOR_2_NAME),
        (CONF_SENSOR_3, CONF_SENSOR_3_NAME),
        (CONF_SENSOR_4, CONF_SENSOR_4_NAME),
        (CONF_SENSOR_5, CONF_SENSOR_5_NAME),
        (CONF_SENSOR_6, CONF_SENSOR_6_NAME),
    ]
    
    for sensor_key, name_key in sensor_configs:
        # Only set default if value exists and is not None/empty
        sensor_default = defaults.get(sensor_key)
        if sensor_default and sensor_default.strip():
            schema_dict[vol.Optional(sensor_key, default=sensor_default)] = sensor_selector
        else:
            # No default - this allows the field to be empty
            schema_dict[vol.Optional(sensor_key)] = sensor_selector
        
        # Name fields always get defaults (empty string is fine)
        schema_dict[vol.Optional(name_key, default=defaults.get(name_key, ""))] = str

    return vol.Schema(schema_dict)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, str]:
    """Validate the user input and create entry title.

    Args:
        hass: Home Assistant instance
        data: User input data from the config flow

    Returns:
        dict: Contains the title for the config entry

    Raises:
        InvalidURL: If the provided URL is not valid
    """
    # Validate URL format
    if not data[CONF_URL].startswith(("http://", "https://")):
        raise InvalidURL("URL must start with http:// or https://")

    # Validate that CO2 sensor exists in Home Assistant
    if data.get(CONF_CO2_SENSOR):
        co2_state = hass.states.get(data[CONF_CO2_SENSOR])
        if not co2_state:
            raise InvalidEntity(f"CO2 sensor {data[CONF_CO2_SENSOR]} not found")

    # Validate optional sensors if they are provided and not None/empty
    sensor_keys = [CONF_SENSOR_1, CONF_SENSOR_2, CONF_SENSOR_3, 
                   CONF_SENSOR_4, CONF_SENSOR_5, CONF_SENSOR_6]
    
    for sensor_key in sensor_keys:
        sensor_id = data.get(sensor_key)
        if sensor_id and sensor_id != "None" and isinstance(sensor_id, str) and sensor_id.strip():
            sensor_state = hass.states.get(sensor_id)
            if not sensor_state:
                raise InvalidEntity(f"Sensor {sensor_id} not found")

    # Create a descriptive title for the integration entry
    title_parts = ["TRMNL Weather"]

    # Add CO2 sensor info to title since it's required
    if data.get(CONF_CO2_SENSOR):
        # Use custom name if provided, otherwise fall back to entity name
        sensor_name = data.get(CONF_CO2_NAME) or get_sensor_friendly_name(
            hass, data[CONF_CO2_SENSOR]
        )
        title_parts.append(f"({sensor_name})")

    return {"title": " ".join(title_parts)}


# =============================================================================
# Config Flow Classes
# =============================================================================


class TrmnlWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a multi-step config flow for TRMNL Weather Station integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.data = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial setup step (basic configuration).

        This is step 1/2 where users configure the essential settings:
        - TRMNL webhook URL
        - Required CO2 sensor
        - Update interval

        Args:
            user_input: The data submitted by the user, if any

        Returns:
            FlowResult: Either shows the form or proceeds to sensors step
        """
        errors = {}

        # Process form submission
        if user_input is not None:
            try:
                # Basic validation for URL
                if not user_input[CONF_URL].startswith(("http://", "https://")):
                    raise InvalidURL("URL must start with http:// or https://")

                # Validate CO2 sensor exists
                if user_input.get(CONF_CO2_SENSOR):
                    co2_state = self.hass.states.get(user_input[CONF_CO2_SENSOR])
                    if not co2_state:
                        raise InvalidEntity(f"CO2 sensor {user_input[CONF_CO2_SENSOR]} not found")

                # Store the basic configuration
                self.data.update(user_input)

                # Proceed to sensors configuration step
                return await self.async_step_sensors()

            except InvalidURL:
                errors["base"] = "invalid_url"
                _LOGGER.warning("Invalid URL provided: %s", user_input.get(CONF_URL))

            except InvalidEntity as ex:
                errors["base"] = "invalid_entity"
                _LOGGER.warning("Invalid entity: %s", ex)

            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during basic config: %s", ex)
                errors["base"] = "unknown"

        # Show the basic configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=create_basic_schema(),
            errors=errors,
            description_placeholders={
                "url_example": DEFAULT_URL,
                "min_interval": str(
                    MIN_TIME_BETWEEN_UPDATES // 60
                ),  # Convert to minutes
                "max_interval": str(86400 // 3600),  # Convert to hours
            },
        )

    async def async_step_sensors(self, user_input: dict | None = None) -> FlowResult:
        """Handle the sensors configuration step.

        This is step 2/2 where users can optionally add up to 6 additional
        sensors beyond the required CO2 sensor.

        Args:
            user_input: The data submitted by the user, if any

        Returns:
            FlowResult: Either shows the form or creates the config entry
        """
        # Process form submission
        if user_input is not None:
            # Clean up sensor data (convert empty strings to None)
            cleaned_input = clean_sensor_data(user_input)
            
            # Merge with basic configuration from step 1
            final_data = {**self.data, **cleaned_input}

            try:
                # Validate complete configuration and get entry info
                info = await validate_input(self.hass, final_data)

                # Create the config entry
                return self.async_create_entry(title=info["title"], data=final_data)

            except InvalidURL:
                # This shouldn't happen since we validated in step 1, but just in case
                _LOGGER.error("URL validation failed in sensors step")
                return await self.async_step_user()

            except InvalidEntity as ex:
                _LOGGER.warning("Invalid entity in sensors step: %s", ex)
                return self.async_show_form(
                    step_id="sensors",
                    data_schema=create_sensors_schema(),
                    errors={"base": "invalid_entity"},
                    description_placeholders={
                        "co2_sensor": self.data.get(CONF_CO2_SENSOR, "Unknown"),
                        "co2_name": self.data.get(CONF_CO2_NAME, "CO2"),
                    },
                )

            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during sensors config: %s", ex)
                # Go back to step 1 with error
                return self.async_show_form(
                    step_id="user",
                    data_schema=create_basic_schema(defaults=self.data),
                    errors={"base": "unknown"},
                )

        # Show the sensors configuration form
        return self.async_show_form(
            step_id="sensors",
            data_schema=create_sensors_schema(),
            description_placeholders={
                "co2_sensor": self.data.get(CONF_CO2_SENSOR, "Unknown"),
                "co2_name": self.data.get(CONF_CO2_NAME, "CO2"),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow for reconfiguration.

        Args:
            config_entry: The existing config entry to modify

        Returns:
            TrmnlWeatherOptionsFlowHandler: The options flow handler
        """
        return TrmnlWeatherOptionsFlowHandler(config_entry)


class TrmnlWeatherOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for TRMNL Weather Station integration.

    This allows users to modify their configuration after the initial setup.
    For options, we use a single step since users are already familiar with
    the configuration at this point.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow.

        Args:
            config_entry: The config entry to modify
        """
        super().__init__()

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Handle the options configuration step.

        Args:
            user_input: The data submitted by the user, if any

        Returns:
            FlowResult: Either shows the form or creates the options entry
        """
        errors = {}

        # Process form submission
        if user_input is not None:
            try:
                # Validate URL if it was changed
                if not user_input[CONF_URL].startswith(("http://", "https://")):
                    raise InvalidURL("URL must start with http:// or https://")

                # Clean up sensor data (convert empty strings to None)
                cleaned_input = clean_sensor_data(user_input)

                # Validate sensors exist
                await validate_input(self.hass, cleaned_input)

                return self.async_create_entry(title="", data=cleaned_input)

            except InvalidURL:
                errors["base"] = "invalid_url"
                _LOGGER.warning("Invalid URL in options: %s", user_input.get(CONF_URL))

            except InvalidEntity as ex:
                errors["base"] = "invalid_entity"
                _LOGGER.warning("Invalid entity in options: %s", ex)

            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in options flow: %s", ex)
                errors["base"] = "unknown"

        # Get current configuration (options override data)
        current_config = {**self.config_entry.data, **self.config_entry.options}

        # Convert None values to empty strings for form display
        form_defaults = {}
        for key, value in current_config.items():
            if key in [CONF_SENSOR_1, CONF_SENSOR_2, CONF_SENSOR_3, 
                      CONF_SENSOR_4, CONF_SENSOR_5, CONF_SENSOR_6]:
                # Convert None to empty string, but keep actual entity IDs
                if value is None:
                    form_defaults[key] = ""
                else:
                    form_defaults[key] = value
            else:
                form_defaults[key] = value

        # Log current configuration for debugging
        _LOGGER.debug("Current configuration for options flow: %s", current_config)

        # Create combined schema for options
        combined_schema = self._create_combined_options_schema(form_defaults)

        # Show the options form with current values as defaults
        return self.async_show_form(
            step_id="init",
            data_schema=combined_schema,
            errors=errors,
            description_placeholders={
                "current_url": current_config.get(CONF_URL, "Not set"),
                "current_co2": current_config.get(CONF_CO2_SENSOR, "Not set"),
                "current_interval": str(
                    current_config.get("update_interval", MIN_TIME_BETWEEN_UPDATES)
                    // 60
                ),
            },
        )

    def _create_combined_options_schema(self, defaults: dict) -> vol.Schema:
        """Create the combined options schema with all fields."""
        co2_filter, sensor_filter = get_entity_selectors()

        # Create EntitySelector that allows empty selection
        sensor_selector = EntitySelector(EntitySelectorConfig(
            filter=sensor_filter,
            multiple=False,
        ))

        schema_dict = {
            vol.Required(
                CONF_URL, default=defaults.get(CONF_URL, DEFAULT_URL)
            ): str,
            vol.Required(
                CONF_CO2_SENSOR, default=defaults.get(CONF_CO2_SENSOR)
            ): EntitySelector(EntitySelectorConfig(filter=co2_filter)),
            vol.Optional(
                CONF_CO2_NAME, default=defaults.get(CONF_CO2_NAME, "CO2")
            ): str,
            vol.Optional(
                "update_interval",
                default=defaults.get("update_interval", MIN_TIME_BETWEEN_UPDATES),
            ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400)),
        }

        # Add sensor fields, only setting defaults if they have actual values
        sensor_configs = [
            (CONF_SENSOR_1, CONF_SENSOR_1_NAME),
            (CONF_SENSOR_2, CONF_SENSOR_2_NAME),
            (CONF_SENSOR_3, CONF_SENSOR_3_NAME),
            (CONF_SENSOR_4, CONF_SENSOR_4_NAME),
            (CONF_SENSOR_5, CONF_SENSOR_5_NAME),
            (CONF_SENSOR_6, CONF_SENSOR_6_NAME),
        ]
        
        for sensor_key, name_key in sensor_configs:
            # Only set default if value exists and is not None/empty
            sensor_default = defaults.get(sensor_key)
            if sensor_default and sensor_default.strip() and sensor_default != "None":
                schema_dict[vol.Optional(sensor_key, default=sensor_default)] = sensor_selector
            else:
                # No default - this allows the field to be empty
                schema_dict[vol.Optional(sensor_key)] = sensor_selector
            
            # Name fields always get defaults (empty string is fine)
            schema_dict[vol.Optional(name_key, default=defaults.get(name_key, ""))] = str

        return vol.Schema(schema_dict)


# =============================================================================
# Custom Exceptions
# =============================================================================


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the service."""


class InvalidURL(HomeAssistantError):
    """Error to indicate the provided URL is invalid."""


class InvalidEntity(HomeAssistantError):
    """Error to indicate an entity ID is invalid or not found."""