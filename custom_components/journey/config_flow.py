"""Adds config flow for Journey."""
import voluptuous as vol
from homeassistant import config_entries

from .api import JourneyApiClient
from .const import (
    CONF_DESTINATION,
    CONF_GMAPS_TOKEN,
    CONF_NAME,
    CONF_ORIGIN,
    DOMAIN,
)


class JourneyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    """Config flow for journey."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            valid = await self._test_credentials(user_input[CONF_GMAPS_TOKEN])
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_ORIGIN): str,
                    vol.Required(CONF_DESTINATION): str,
                    vol.Required(CONF_GMAPS_TOKEN): str,
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, gmaps_token):
        """Return true if credentials is valid."""
        try:
            client = JourneyApiClient(gmaps_token)
            await client.test_credentials()
            return True
        except Exception:  # pylint: disable=broad-except
            pass
        return False
