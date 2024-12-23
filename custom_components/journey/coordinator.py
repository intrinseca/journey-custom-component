"""Data update coordinator for routing APIs."""

import logging
from datetime import timedelta

from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiClient, TravelTimeData
from .const import (
    DOMAIN,
)
from .helpers import find_coordinates

SCAN_INTERVAL = timedelta(minutes=5)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class JourneyDataUpdateCoordinator(DataUpdateCoordinator[TravelTimeData]):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ApiClient,
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

    async def update(self) -> TravelTimeData:
        """Update data via library."""
        origin_name, origin_coords = find_coordinates(self.hass, self._origin_entity_id)
        destination_name, destination_coords = find_coordinates(
            self.hass, self._destination_entity_id
        )

        if origin_coords is None:
            raise UpdateFailed("Could not find destination coords")
        if destination_coords is None:
            raise UpdateFailed("Could not find origin coords")

        try:
            if origin_coords == destination_coords:
                _LOGGER.info("origin is equal to destination")
                return TravelTimeData(
                    origin_name if origin_name is not None else origin_coords,
                    destination_name
                    if destination_name is not None
                    else destination_coords,
                    0,
                    0,
                    0,
                )
            else:
                return await self.api.async_get_traveltime(
                    origin_coords, destination_coords
                )

        except Exception as exception:
            raise UpdateFailed(str(exception)) from exception
