"""Constants for Airbnk cloud-based integration."""

from homeassistant.const import CONF_TOKEN

DOMAIN = "airbnk_cloud"

CONF_USERID = "userId"
CONF_TOKENSET = CONF_TOKEN + "set"
CONF_UUID = "uuid"
CONF_LOCKSTATUS = "lockStatus"

AIRBNK_DATA = "airbnk_data"
AIRBNK_API = "airbnk_api"
AIRBNK_DEVICES = "airbnk_devices"
AIRBNK_DISCOVERY_NEW = "airbnk_discovery_new_{}"

TIMEOUT = 60
