"""Custom integration to integrate Journey with Home Assistant.

For more details about this integration, please refer to
https://github.com/intrinseca/journey
"""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.core_config import Config

from .api import ApiClient, GoogleMapsApiClient, HereMapsApiClient
from .const import (
    CONF_API_TOKEN,
    CONF_DESTINATION,
    CONF_ORIGIN,
    CONF_SELECTED_API,
    CONF_SELECTED_API_GOOGLE,
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

    client: ApiClient
    if entry.data.get(CONF_SELECTED_API) == CONF_SELECTED_API_GOOGLE:
        client = GoogleMapsApiClient(entry.data[CONF_API_TOKEN])
    else:
        client = HereMapsApiClient(entry.data[CONF_API_TOKEN])

    coordinator = JourneyDataUpdateCoordinator(
        hass,
        client=client,
        origin=entry.data[CONF_ORIGIN],
        destination=entry.data[CONF_DESTINATION],
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)
    return True


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug(
        "Migrating configuration from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )

    if config_entry.version > 3:
        # This means the user has downgraded from a future version
        return False

    if config_entry.version == 2:
        new_data = {**config_entry.data}
        new_data[CONF_API_TOKEN] = new_data["gmaps_token"]
        del new_data["gmaps_token"]
        new_data[CONF_SELECTED_API] = CONF_SELECTED_API_GOOGLE

        hass.config_entries.async_update_entry(
            config_entry, data=new_data, minor_version=0, version=3
        )

    _LOGGER.debug(
        "Migration to configuration version %s.%s successful",
        config_entry.version,
        config_entry.minor_version,
    )

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
