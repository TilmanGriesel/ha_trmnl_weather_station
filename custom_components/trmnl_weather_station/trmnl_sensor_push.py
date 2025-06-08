"""TRMNL sensor push functionality for labeled entities."""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)


def get_trmnl_entities(hass: HomeAssistant):
    """Retrieve all entities labeled with 'TRMNL'."""
    template_str = "{{ label_entities('TRMNL') }}"
    template = Template(template_str, hass)
    return template.async_render()


def setup_platform(hass: HomeAssistant, entry) -> None:
    """Set up the TRMNL sensor push platform."""
    def process_trmnl_entities():
        """Process and log all TRMNL-labeled entities."""
        trmnl_entities = get_trmnl_entities(hass)

        _LOGGER.info(f"Found {len(trmnl_entities)} entities with TRMNL label")
        for entity_id in trmnl_entities:
            _LOGGER.debug(f"TRMNL Entity Found: {entity_id}")

    hass.add_job(process_trmnl_entities)