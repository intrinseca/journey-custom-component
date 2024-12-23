"""Sample API Client."""

import asyncio
import logging
import math
import typing
from dataclasses import dataclass
from datetime import datetime

from googlemaps import Client
from here_location_services import LS

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)


@dataclass
class TravelTimeData:
    """Container for API results."""

    origin: str
    destination: str
    travel_time_secs: float
    travel_time_traffic_secs: float
    distance_m: float

    @property
    def travel_time_min(self):
        """Get the nominal duration of the journey in minutes."""
        return (
            round(self.travel_time_secs / 60)
            if not math.isnan(self.travel_time_secs)
            else None
        )

    @property
    def travel_time_traffic_min(self):
        """Get the current duration of the journey in minutes."""
        return (
            round(self.travel_time_traffic_secs / 60)
            if not math.isnan(self.travel_time_traffic_secs)
            else None
        )

    @property
    def delay(self):
        """Get the delay to the journey in seconds."""
        return self.travel_time_traffic_secs - self.travel_time_secs

    @property
    def delay_min(self):
        """Get the delay to the journey in minutes."""
        return round(self.delay / 60) if not math.isnan(self.delay) else None

    @property
    def delay_factor(self):
        """Get the delay to the journey as a percentage."""
        return (
            round(100 * self.delay / self.travel_time_secs)
            if self.travel_time_secs > 0
            else 0
        )


class ApiClient(typing.Protocol):
    """Interface for Travel Time APIs."""

    def get_traveltime(self, origin: str, destination: str) -> TravelTimeData:
        """Get travel time now from origin to destination."""
        ...

    async def async_get_traveltime(
        self, origin: str, destination: str
    ) -> TravelTimeData:
        """Get travel time now from origin to destination (async)."""
        ...

    async def test_credentials(self) -> bool:
        """Test API connection is functioning."""
        ...


class GoogleMapsApiClient(ApiClient):
    """API client for the Google Travel Time API."""

    def __init__(self, gmaps_token: str) -> None:
        """Initialise the API client."""
        self._gmaps_token = gmaps_token
        self._gmaps_client = Client(gmaps_token, timeout=TIMEOUT)

    def get_traveltime(self, origin: str, destination: str) -> TravelTimeData:
        """Get the travel time from origin to destination using Google Maps."""

        result = self._gmaps_client.distance_matrix(
            origins=[origin],
            destinations=[destination],
            mode="driving",
            departure_time=datetime.now(),
        )
        return TravelTimeData(
            origin,
            result["destination_addresses"][0],
            result["rows"][0]["elements"][0]["duration"]["value"],
            result["rows"][0]["elements"][0]["duration_in_traffic"]["value"],
            result["rows"][0]["elements"][0]["distance"]["value"],
        )

    async def async_get_traveltime(
        self, origin: str, destination: str
    ) -> TravelTimeData:
        """Get the travel time from origin to destination using Google Maps."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get_traveltime, origin, destination
        )

    async def test_credentials(self) -> bool:
        """Check the Google Maps API credentials."""

        def test_api():
            try:
                self._gmaps_client.distance_matrix(
                    origins=[(51.478, 0)], destinations=[(51.748, 0.02)], mode="driving"
                )
            except Exception as ex:
                _LOGGER.error("Failed to validate credentials - %s", ex)
                raise

        return await asyncio.get_event_loop().run_in_executor(None, test_api)


class HereMapsApiClient(ApiClient):
    """API client for the HERE Maps Routing Time API."""

    def __init__(self, here_token: str) -> None:
        """Initialise the API client."""
        self._here_token = here_token
        self._here_client = LS(api_key=here_token)

    def get_traveltime(self, origin: str, destination: str) -> TravelTimeData:
        """Get the travel time from origin to destination using Google Maps."""
        origin_split = [float(x) for x in origin.split(",")]
        destination_split = [float(x) for x in destination.split(",")]

        result = self._here_client.car_route(
            origin=origin_split,
            destination=destination_split,
            return_results=[
                "summary",
            ],
        )

        return TravelTimeData(
            origin,
            destination,
            result.routes[0]["sections"][0]["summary"]["baseDuration"],
            result.routes[0]["sections"][0]["summary"]["duration"],
            result.routes[0]["sections"][0]["summary"]["length"],
        )

    async def async_get_traveltime(
        self, origin: str, destination: str
    ) -> TravelTimeData:
        """Get the travel time from origin to destination using Google Maps."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get_traveltime, origin, destination
        )

    async def test_credentials(self) -> bool:
        """Check the HERE API credentials."""

        def test_api():
            try:
                self._here_client.car_route(
                    origins=[(51.478, 0)], destinations=[(51.748, 0.02)]
                )
            except Exception as ex:
                _LOGGER.error("Failed to validate credentials - %s", ex)
                raise

        return await asyncio.get_event_loop().run_in_executor(None, test_api)
