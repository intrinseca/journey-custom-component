"""Constants for Journey."""
# Base component constants

NAME = "Journey"
DOMAIN = "journey"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1.0"

ISSUE_URL = "https://github.com/intrinseca/journey-custom-component/issues"

# Icons
ICON = "mdi:map-marker-right"

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_NAME = "name"
CONF_API_TOKEN = "api_token"
CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_SELECTED_API = "selected_api"

CONF_SELECTED_API_HERE = "HERE"
CONF_SELECTED_API_GOOGLE = "Google"

# Defaults
DEFAULT_NAME = DOMAIN
