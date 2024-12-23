"""Custom integration to integrate Journey with Home Assistant.

For more details about this integration, please refer to
https://github.com/intrinseca/journey
"""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.core_config import Config

from .api import GoogleMapsApiClient, HereMapsApiClient
from .const import (
    CONF_DESTINATION,
    CONF_GMAPS_TOKEN,
    CONF_HERE_TOKEN,
    CONF_ORIGIN,
    CONF_SELECTED_API,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import JourneyDataUpdateCoordinator

_LOGGER: logging.Logger = logging.getLogger(__package__)


# pylint: disable=unused-argument
async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    origin = entry.data.get(CONF_ORIGIN)
    destination = entry.data.get(CONF_DESTINATION)

    gmaps_client = GoogleMapsApiClient(entry.data.get(CONF_GMAPS_TOKEN))
    here_client = HereMapsApiClient(entry.data.get(CONF_HERE_TOKEN))

    coordinator = JourneyDataUpdateCoordinator(
        hass,
        client=gmaps_client
        if entry.data.get(CONF_SELECTED_API) == "Google"
        else here_client,
        origin=origin,
        destination=destination,
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
