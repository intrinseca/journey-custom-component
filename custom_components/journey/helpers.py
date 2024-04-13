"""Helpers for handling location entities."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import location

_LOGGER: logging.Logger = logging.getLogger(__package__)


def find_coordinates(
    hass: HomeAssistant, name: str, recursion_history: list | None = None
) -> tuple[str | None, str | None]:
    """Try to resolve the a location from a supplied name or entity_id.

    Will recursively resolve an entity if pointed to by the state of the supplied
    entity.

    Returns coordinates in the form of '90.000,180.000', an address or
    the state of the last resolved entity.
    """
    # Check if a friendly name of a zone was supplied
    if (zone_coords := location.resolve_zone(hass, name)) is not None:
        _LOGGER.debug(
            "%s, getting zone location",
            name,
        )
        return (name, zone_coords)

    # Check if an entity_id was supplied.
    if (entity_state := hass.states.get(name)) is None:
        _LOGGER.debug("Unable to find entity %s", name)
        return None, name

    # Check if entity_state is a zone
    zone_entity = hass.states.get(f"zone.{entity_state.state}")
    if location.has_location(zone_entity):  # type: ignore[arg-type]
        _LOGGER.debug(
            "%s is in %s, getting zone location",
            name,
            zone_entity.entity_id,  # type: ignore[union-attr]
        )
        return zone_entity.name, location._get_location_from_attributes(zone_entity)  # type: ignore[arg-type]

    # Check if entity_state is a friendly name of a zone
    if (zone_coords := location.resolve_zone(hass, entity_state.state)) is not None:
        _LOGGER.debug(
            "%s is in %s, getting zone location",
            name,
            entity_state.state,  # type: ignore[union-attr]
        )
        return entity_state.state, zone_coords

    # Check if the entity_state has location attributes
    if location.has_location(entity_state):
        _LOGGER.debug("%s has coords", name)
        return entity_state.name, location._get_location_from_attributes(entity_state)

    # Check if entity_state is an entity_id
    if recursion_history is None:
        recursion_history = []
    recursion_history.append(name)
    if entity_state.state in recursion_history:
        _LOGGER.error(
            (
                "Circular reference detected while trying to find coordinates of an"
                " entity. The state of %s has already been checked"
            ),
            entity_state.state,
        )
        return None, None
    _LOGGER.debug("Getting nested entity for state: %s", entity_state.state)
    nested_entity = hass.states.get(entity_state.state)
    if nested_entity is not None:
        _LOGGER.debug("Resolving nested entity_id: %s", entity_state.state)
        return find_coordinates(hass, entity_state.state, recursion_history)

    # Might be an address, coordinates or anything else.
    # This has to be checked by the caller.
    _LOGGER.debug("%s is in (raw state) '%s'", name, entity_state.state)
    return None, entity_state.state
