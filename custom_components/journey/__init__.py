"""Custom integration to integrate Journey with Home Assistant.

For more details about this integration, please refer to
https://github.com/intrinseca/journey
"""
import asyncio
import logging
import math
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, Event, HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import JourneyApiClient
from .const import (
    CONF_DESTINATION,
    CONF_GMAPS_TOKEN,
    CONF_ORIGIN,
    DOMAIN,
    PLATFORMS,
)
from .helpers import get_location_entity, get_location_from_attributes

SCAN_INTERVAL = timedelta(minutes=5)

_LOGGER: logging.Logger = logging.getLogger(__package__)


# pylint: disable=unused-argument
async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    token = entry.data.get(CONF_GMAPS_TOKEN)

    origin = entry.data.get(CONF_ORIGIN)
    destination = entry.data.get(CONF_DESTINATION)
    client = JourneyApiClient(token)

    coordinator = JourneyDataUpdateCoordinator(
        hass, client=client, origin=origin, destination=destination
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)  # type: ignore
            )

    entry.add_update_listener(async_reload_entry)
    return True


@dataclass
class JourneyTravelTime:
    """Container for Journey time data."""

    travel_time: dict
    destination: str

    @property
    def travel_time_values(self) -> dict:
        """Flatten the travel time results dictionary."""
        if self.travel_time is None:
            return {}

        return {k: v["value"] for k, v in self.travel_time.items() if k != "status"}

    @property
    def duration(self):
        """Get the nominal duration of the journey in seconds."""
        if self.travel_time_values is None:
            return float("nan")

        return self.travel_time_values.get("duration", float("nan"))

    @property
    def duration_min(self):
        """Get the nominal duration of the journey in minutes."""
        return round(self.duration / 60) if not math.isnan(self.duration) else None

    @property
    def duration_in_traffic(self):
        """Get the current duration of the journey in seconds."""
        if self.travel_time_values is None:
            return float("nan")

        return self.travel_time_values.get("duration_in_traffic", self.duration)

    @property
    def duration_in_traffic_min(self):
        """Get the current duration of the journey in minutes."""
        return (
            round(self.duration_in_traffic / 60)
            if not math.isnan(self.duration_in_traffic)
            else None
        )

    @property
    def delay(self):
        """Get the delay to the journey in seconds."""
        return self.duration_in_traffic - self.duration

    @property
    def delay_min(self):
        """Get the delay to the journey in minutes."""
        return round(self.delay / 60) if not math.isnan(self.delay) else None

    @property
    def delay_factor(self):
        """Get the delay to the journey as a percentage."""
        return round(100 * self.delay / self.duration) if self.duration > 0 else 0


class JourneyDataUpdateCoordinator(DataUpdateCoordinator[JourneyTravelTime]):  # type: ignore
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: JourneyApiClient,
        origin: str,
        destination: str,
    ) -> None:
        """Initialize."""

        self.api = client

        self._origin_entity_id = origin
        self._destination_entity_id = destination

        async_track_state_change_event(
            hass, self._origin_entity_id, self._handle_origin_state_change
        )

        async_track_state_change_event(
            hass, self._destination_entity_id, self._handle_destination_state_change
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            update_method=self.update,
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=1800, immediate=True
            ),
        )

    async def _handle_origin_state_change(self, event: Event):
        if event.data["old_state"].state == event.data["new_state"].state:
            _LOGGER.debug("Origin updated without state change, requesting refresh")
            await self.async_request_refresh()
        else:
            _LOGGER.debug("Origin updated *with* state change, forcing refresh")
            await self.async_refresh()

    async def _handle_destination_state_change(self, event: Event):
        await self.async_refresh()

    async def update(self):
        """Update data via library."""
        try:
            origin_entity = get_location_entity(self.hass, self._origin_entity_id)
            origin = get_location_from_attributes(origin_entity)

            destination_entity = get_location_entity(
                self.hass, self._destination_entity_id
            )

            if destination_entity is None:
                _LOGGER.error("Unable to get destination coordinates")
                traveltime = JourneyTravelTime(None, None)
            elif origin_entity.entity_id == destination_entity.entity_id:
                _LOGGER.info("origin is equal to destination zone")
                traveltime = JourneyTravelTime(
                    {"duration": {"value": 0}, "duration_in_traffic": {"value": 0}},
                    origin_entity.name,
                )
            else:
                destination = get_location_from_attributes(destination_entity)
                destination_name = destination_entity.name
                traveltime = JourneyTravelTime(
                    travel_time=await self.api.async_get_traveltime(
                        origin, destination
                    ),
                    destination=destination_name,
                )

            return traveltime
        except Exception as exception:
            raise UpdateFailed() from exception


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
