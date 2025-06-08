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
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    BooleanSelector,
)

from .const import (
    DOMAIN,
    CONF_URL,
    DEFAULT_UPDATE_INTERVAL,
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
    DEFAULT_URL,
    SENSOR_DEVICE_CLASSES,
)

_LOGGER = logging.getLogger(__name__)


def get_entity_selectors() -> tuple[dict, dict]:
    """Create entity selectors for CO2 and general sensors."""
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
    """Get a friendly name for a sensor entity."""
    entity_registry = er.async_get(hass)
    entity = entity_registry.async_get(entity_id)

    if entity and entity.original_name:
        return entity.original_name

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
            if not value or (isinstance(value, str) and (not value.strip() or value.strip() == "None")):
                cleaned[key] = None
    
    return cleaned


def create_basic_schema(defaults: dict = None) -> vol.Schema:
    """Create the basic configuration schema for step 1."""
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
            default=defaults.get("update_interval", DEFAULT_UPDATE_INTERVAL),
        ): NumberSelector(NumberSelectorConfig(
            min=5,
            max=1440,
            step=5,
            unit_of_measurement="minutes",
            mode=NumberSelectorMode.SLIDER
        )),
    }

    return vol.Schema(schema_dict)


def create_sensors_schema(defaults: dict = None) -> vol.Schema:
    """Create the additional sensors schema for step 2."""
    if defaults is None:
        defaults = {}

    _, sensor_filter = get_entity_selectors()

    sensor_selector = EntitySelector(EntitySelectorConfig(
        filter=sensor_filter,
        multiple=False,
    ))

    schema_dict = {}
    
    # Add sensor configurations first
    sensor_configs = [
        (CONF_SENSOR_1, CONF_SENSOR_1_NAME),
        (CONF_SENSOR_2, CONF_SENSOR_2_NAME),
        (CONF_SENSOR_3, CONF_SENSOR_3_NAME),
        (CONF_SENSOR_4, CONF_SENSOR_4_NAME),
        (CONF_SENSOR_5, CONF_SENSOR_5_NAME),
        (CONF_SENSOR_6, CONF_SENSOR_6_NAME),
    ]
    
    for sensor_key, name_key in sensor_configs:
        sensor_default = defaults.get(sensor_key)
        if sensor_default and sensor_default.strip():
            schema_dict[vol.Optional(sensor_key, default=sensor_default)] = sensor_selector
        else:
            schema_dict[vol.Optional(sensor_key)] = sensor_selector
        
        schema_dict[vol.Optional(name_key, default=defaults.get(name_key, ""))] = str

    # Add decimal places at the end, before include IDs
    schema_dict[vol.Optional(
        CONF_DECIMAL_PLACES,
        default=defaults.get(CONF_DECIMAL_PLACES, DEFAULT_DECIMAL_PLACES),
    )] = vol.All(vol.Coerce(int), vol.Range(min=0, max=4))
    
    # Add include IDs last with development category
    schema_dict[vol.Optional(CONF_INCLUDE_IDS, default=defaults.get(CONF_INCLUDE_IDS, False))] = BooleanSelector()

    return vol.Schema(schema_dict)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, str]:
    """Validate the user input and create entry title."""
    if not data[CONF_URL].startswith(("http://", "https://")):
        raise InvalidURL("URL must start with http:// or https://")

    if data.get(CONF_CO2_SENSOR):
        co2_state = hass.states.get(data[CONF_CO2_SENSOR])
        if not co2_state:
            raise InvalidEntity(f"CO2 sensor {data[CONF_CO2_SENSOR]} not found")

    sensor_keys = [CONF_SENSOR_1, CONF_SENSOR_2, CONF_SENSOR_3, 
                   CONF_SENSOR_4, CONF_SENSOR_5, CONF_SENSOR_6]
    
    for sensor_key in sensor_keys:
        sensor_id = data.get(sensor_key)
        if sensor_id and sensor_id != "None" and isinstance(sensor_id, str) and sensor_id.strip():
            sensor_state = hass.states.get(sensor_id)
            if not sensor_state:
                raise InvalidEntity(f"Sensor {sensor_id} not found")

    title_parts = ["TRMNL Weather"]

    if data.get(CONF_CO2_SENSOR):
        sensor_name = data.get(CONF_CO2_NAME) or get_sensor_friendly_name(
            hass, data[CONF_CO2_SENSOR]
        )
        title_parts.append(f"({sensor_name})")

    return {"title": " ".join(title_parts)}


class TrmnlWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a multi-step config flow for TRMNL Weather Station integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.data = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial setup step (basic configuration)."""
        errors = {}

        if user_input is not None:
            try:
                if not user_input[CONF_URL].startswith(("http://", "https://")):
                    raise InvalidURL("URL must start with http:// or https://")

                if user_input.get(CONF_CO2_SENSOR):
                    co2_state = self.hass.states.get(user_input[CONF_CO2_SENSOR])
                    if not co2_state:
                        raise InvalidEntity(f"CO2 sensor {user_input[CONF_CO2_SENSOR]} not found")

                self.data.update(user_input)
                return await self.async_step_sensors()

            except InvalidURL:
                errors["base"] = "invalid_url"
                _LOGGER.warning("Invalid URL provided: %s", user_input.get(CONF_URL))

            except InvalidEntity as ex:
                errors["base"] = "invalid_entity"
                _LOGGER.warning("Invalid entity: %s", ex)

            except Exception as ex:
                _LOGGER.exception("Unexpected exception during basic config: %s", ex)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=create_basic_schema(),
            errors=errors,
            description_placeholders={
                "url_example": DEFAULT_URL,
                "min_interval": str(5),
                "max_interval": str(24),
            },
        )

    async def async_step_sensors(self, user_input: dict | None = None) -> FlowResult:
        """Handle the sensors configuration step."""
        if user_input is not None:
            cleaned_input = clean_sensor_data(user_input)
            final_data = {**self.data, **cleaned_input}

            try:
                info = await validate_input(self.hass, final_data)
                return self.async_create_entry(title=info["title"], data=final_data)

            except InvalidURL:
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

            except Exception as ex:
                _LOGGER.exception("Unexpected exception during sensors config: %s", ex)
                return self.async_show_form(
                    step_id="user",
                    data_schema=create_basic_schema(defaults=self.data),
                    errors={"base": "unknown"},
                )

        return self.async_show_form(
            step_id="sensors",
            data_schema=create_sensors_schema(),
            description_placeholders={
                "co2_sensor": self.data.get(CONF_CO2_SENSOR, "Unknown"),
                "co2_name": self.data.get(CONF_CO2_NAME, "CO2"),
                "decimal_places": str(self.data.get(CONF_DECIMAL_PLACES, DEFAULT_DECIMAL_PLACES)),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow for reconfiguration."""
        return TrmnlWeatherOptionsFlowHandler(config_entry)


class TrmnlWeatherOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for TRMNL Weather Station integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        super().__init__()

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Handle the options configuration step."""
        errors = {}

        if user_input is not None:
            try:
                if not user_input[CONF_URL].startswith(("http://", "https://")):
                    raise InvalidURL("URL must start with http:// or https://")

                cleaned_input = clean_sensor_data(user_input)
                await validate_input(self.hass, cleaned_input)

                return self.async_create_entry(title="", data=cleaned_input)

            except InvalidURL:
                errors["base"] = "invalid_url"
                _LOGGER.warning("Invalid URL in options: %s", user_input.get(CONF_URL))

            except InvalidEntity as ex:
                errors["base"] = "invalid_entity"
                _LOGGER.warning("Invalid entity in options: %s", ex)

            except Exception as ex:
                _LOGGER.exception("Unexpected exception in options flow: %s", ex)
                errors["base"] = "unknown"

        current_config = {**self.config_entry.data, **self.config_entry.options}

        form_defaults = {}
        for key, value in current_config.items():
            if key in [CONF_SENSOR_1, CONF_SENSOR_2, CONF_SENSOR_3, 
                      CONF_SENSOR_4, CONF_SENSOR_5, CONF_SENSOR_6]:
                if value is None:
                    form_defaults[key] = ""
                else:
                    form_defaults[key] = value
            else:
                form_defaults[key] = value

        _LOGGER.debug("Current configuration for options flow: %s", current_config)

        combined_schema = self._create_combined_options_schema(form_defaults)

        return self.async_show_form(
            step_id="init",
            data_schema=combined_schema,
            errors=errors,
            description_placeholders={
                "current_url": current_config.get(CONF_URL, "Not set"),
                "current_co2": current_config.get(CONF_CO2_SENSOR, "Not set"),
                "current_interval": str(
                    current_config.get("update_interval", DEFAULT_UPDATE_INTERVAL)
                ),
                "current_decimal_places": str(
                    current_config.get(CONF_DECIMAL_PLACES, DEFAULT_DECIMAL_PLACES)
                ),
            },
        )

    def _create_combined_options_schema(self, defaults: dict) -> vol.Schema:
        """Create the combined options schema with all fields."""
        co2_filter, sensor_filter = get_entity_selectors()

        sensor_selector = EntitySelector(EntitySelectorConfig(
            filter=sensor_filter,
            multiple=False,
        ))

        # Basic configuration fields
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
        }

        # Sensor configuration fields
        sensor_configs = [
            (CONF_SENSOR_1, CONF_SENSOR_1_NAME),
            (CONF_SENSOR_2, CONF_SENSOR_2_NAME),
            (CONF_SENSOR_3, CONF_SENSOR_3_NAME),
            (CONF_SENSOR_4, CONF_SENSOR_4_NAME),
            (CONF_SENSOR_5, CONF_SENSOR_5_NAME),
            (CONF_SENSOR_6, CONF_SENSOR_6_NAME),
        ]
        
        for sensor_key, name_key in sensor_configs:
            sensor_default = defaults.get(sensor_key)
            if sensor_default and sensor_default.strip() and sensor_default != "None":
                schema_dict[vol.Optional(sensor_key, default=sensor_default)] = sensor_selector
            else:
                schema_dict[vol.Optional(sensor_key)] = sensor_selector
            
            schema_dict[vol.Optional(name_key, default=defaults.get(name_key, ""))] = str

        # Misc configuration fields
        
        schema_dict[vol.Optional(
            "update_interval",
            default=defaults.get("update_interval", DEFAULT_UPDATE_INTERVAL),
        )] = NumberSelector(NumberSelectorConfig(
            min=5,
            max=1440,
            step=5,
            unit_of_measurement="minutes",
            mode=NumberSelectorMode.SLIDER
        ))
        
        schema_dict[vol.Optional(
            CONF_DECIMAL_PLACES,
            default=defaults.get(CONF_DECIMAL_PLACES, DEFAULT_DECIMAL_PLACES),
        )] = vol.All(vol.Coerce(int), vol.Range(min=0, max=4))
        
        schema_dict[vol.Optional(CONF_INCLUDE_IDS, default=defaults.get(CONF_INCLUDE_IDS, False))] = BooleanSelector()

        return vol.Schema(schema_dict)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the service."""


class InvalidURL(HomeAssistantError):
    """Error to indicate the provided URL is invalid."""


class InvalidEntity(HomeAssistantError):
    """Error to indicate an entity ID is invalid or not found."""