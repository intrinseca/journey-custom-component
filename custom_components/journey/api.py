"""Sample API Client."""

import asyncio
import logging
from datetime import datetime

from googlemaps import Client

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)


Coordinates = tuple[float, float]


class JourneyApiClient:
    """API client for the Google Travel Time API."""

    def __init__(self, gmaps_token: str) -> None:
        """Initialise the API client."""
        self._gmaps_token = gmaps_token
        self._gmaps_client = Client(gmaps_token, timeout=TIMEOUT)

    def get_traveltime(self, origin: Coordinates, destination: Coordinates):
        """Get the travel time from origin to destination using Google Maps."""
        try:
            result = self._gmaps_client.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode="driving",
                departure_time=datetime.now(),
            )
            return result["destination_addresses"][0], result["rows"][0]["elements"][0]
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Failed to get distances - %s", exception)
            return None

    async def async_get_traveltime(self, origin: Coordinates, destination: Coordinates):
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
