"""Sensor platform for Journey."""

from datetime import datetime, timedelta
from typing import Any

from homeassistant.const import UnitOfTime
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DESTINATION, CONF_NAME, DOMAIN
from .coordinator import JourneyDataUpdateCoordinator


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        [
            JourneyTimeSensor(coordinator, entry),
        ]
    )


class JourneyTimeSensor(CoordinatorEntity[JourneyDataUpdateCoordinator]):
    """Journey Travel Time Sensor Class."""

    _attr_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer"

    def __init__(self, coordinator, config_entry) -> None:
        """Create journey time sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.destination = self.config_entry.data.get(CONF_DESTINATION)

        self._attr_unique_id = self.config_entry.entry_id + "-time"

    @property
    def destination_name(self) -> str:
        """The name of the destination zone."""
        if (dest_state := self.hass.states.get(self.destination)) is not None:
            return dest_state.name

        return self.destination

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "duration": self.coordinator.data.travel_time_secs,
            "duration_in_traffic": self.coordinator.data.travel_time_traffic_secs,
            "delay_minutes": self.coordinator.data.delay_min,
            "delay_factor": self.coordinator.data.delay_factor,
            "destination": self.coordinator.data.destination,
            "eta": (
                (
                    datetime.now().astimezone()
                    + timedelta(seconds=self.coordinator.data.travel_time_traffic_secs)
                ).isoformat()
                if self.coordinator.data.travel_time_traffic_secs
                else None
            ),
        }

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        name = self.config_entry.data.get(CONF_NAME)
        return f"{name} Travel Time"

    @property
    def state(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.travel_time_traffic_min
        else:
            return None
