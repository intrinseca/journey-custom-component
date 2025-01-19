"""Adds config flow for Journey."""

import voluptuous as vol
from homeassistant import config_entries

from .api import GoogleMapsApiClient, HereMapsApiClient
from .const import (
    CONF_DESTINATION,
    CONF_API_TOKEN,
    CONF_NAME,
    CONF_ORIGIN,
    CONF_SELECTED_API,
    CONF_SELECTED_API_GOOGLE,
    CONF_SELECTED_API_HERE,
    DOMAIN,
)


class JourneyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    """Config flow for journey."""

    VERSION = 3
    MINOR_VERSION = 0
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_API_TOKEN], user_input[CONF_SELECTED_API]
            )
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
                    vol.Required(CONF_API_TOKEN): str,
                    vol.Optional(
                        CONF_SELECTED_API, default=CONF_SELECTED_API_GOOGLE
                    ): vol.In(
                        [
                            CONF_SELECTED_API_GOOGLE,
                            CONF_SELECTED_API_HERE,
                        ]
                    ),
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, api_token, selected_api):
        """Return true if credentials is valid."""
        try:
            if selected_api == CONF_SELECTED_API_GOOGLE:
                gmaps_client = GoogleMapsApiClient(api_token)
                await gmaps_client.test_credentials()
            else:
                here_client = HereMapsApiClient(api_token)
                await here_client.test_credentials()

            return True
        except Exception:  # pylint: disable=broad-except
            pass
        return False
