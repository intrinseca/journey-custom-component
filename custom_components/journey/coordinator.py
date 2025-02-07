"""Data update coordinator for routing APIs."""

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiClient, TravelTimeData
from .const import (
    DOMAIN,
)
from .helpers import FindCoordinatesError, LocationData, find_coordinates

SCAN_INTERVAL = timedelta(minutes=5)

_LOGGER: logging.Logger = logging.getLogger(__package__)


@dataclass
class JourneyData:
    """Container class for Journey data."""

    origin: LocationData
    destination: LocationData
    travel_time: TravelTimeData


class JourneyDataUpdateCoordinator(DataUpdateCoordinator[JourneyData]):
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

    async def _handle_origin_state_change(self, event: Event[EventStateChangedData]):
        if (
            event.data["old_state"] is not None
            and event.data["new_state"] is not None
            and event.data["old_state"].state == event.data["new_state"].state
        ):
            _LOGGER.debug("Origin updated without state change, requesting refresh")
            await self.async_request_refresh()
        else:
            _LOGGER.debug("Origin updated *with* state change, forcing refresh")
            await self.async_refresh()

    async def _handle_destination_state_change(
        self, event: Event[EventStateChangedData]
    ):
        await self.async_refresh()

    async def update(self) -> JourneyData:
        """Update data via library."""
        try:
            origin = find_coordinates(self.hass, self._origin_entity_id)
        except FindCoordinatesError as ex:
            raise UpdateFailed(f"Could not find origin coords: {ex!r}")

        try:
            destination = find_coordinates(self.hass, self._destination_entity_id)
        except FindCoordinatesError as ex:
            raise UpdateFailed(f"Could not find destination coords: {ex!r}")

        try:
            if origin.coords == destination.coords:
                _LOGGER.info("origin is equal to destination")
                return JourneyData(
                    origin,
                    destination,
                    TravelTimeData(
                        0,
                        0,
                        0,
                    ),
                )
            else:
                return JourneyData(
                    origin,
                    destination,
                    await self.api.async_get_traveltime(
                        origin.coords, destination.coords
                    ),
                )
        except Exception as exception:
            raise UpdateFailed(repr(exception)) from exception
