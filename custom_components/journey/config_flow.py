"""Adds config flow for Journey."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .api import JourneyApiClient
from .const import (
    CONF_DESTINATION,
    CONF_GMAPS_TOKEN,
    CONF_NAME,
    CONF_ORIGIN,
    DOMAIN,
    PLATFORMS,
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return JourneyOptionsFlowHandler(config_entry)

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


class JourneyOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for journey."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_NAME), data=self.options
        )
