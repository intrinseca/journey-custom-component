"""Sensor platform for Journey."""
from datetime import datetime, timedelta

from homeassistant.const import UnitOfTime
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import JourneyTravelTime
from .const import CONF_DESTINATION, CONF_NAME, DOMAIN


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        [
            JourneyTimeSensor(coordinator, entry),
        ]
    )


class JourneyTimeSensor(CoordinatorEntity[JourneyTravelTime]):  # type: ignore
    """Journey Travel Time Sensor Class."""

    _attr_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer"

    def __init__(self, coordinator, config_entry):
        """Create journey time sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.destination = self.config_entry.data.get(CONF_DESTINATION)

        self._attr_unique_id = self.config_entry.entry_id + "-time"

    @property
    def destination_name(self):
        """The name of the destination zone."""
        if (dest_state := self.hass.states.get(self.destination)) is not None:
            return dest_state.name

        return self.destination

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        raw_result = self.coordinator.data.travel_time_values

        return raw_result | {
            "delay_minutes": self.coordinator.data.delay_min,
            "delay_factor": self.coordinator.data.delay_factor,
            "destination": self.coordinator.data.destination,
            "eta": (
                (
                    datetime.now().astimezone()
                    + timedelta(minutes=self.coordinator.data.duration_in_traffic_min)
                ).isoformat()
                if self.coordinator.data.duration_in_traffic_min
                else None
            ),
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        name = self.config_entry.data.get(CONF_NAME)
        return f"{name} Travel Time"

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.duration_in_traffic_min
        else:
            return None
