"""Config flow for the Airbnk platform."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_CODE, CONF_TOKEN

from .airbnk_api import AirbnkApi
from .const import DOMAIN, CONF_USERID

_LOGGER = logging.getLogger(__name__)

STEP1_SCHEMA = vol.Schema(
    {vol.Required(CONF_EMAIL): str}
)

STEP2_SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str, vol.Required(CONF_CODE): str})


def schema_defaults(schema, dps_list=None, **defaults):
    """Create a new schema with default values filled in."""
    copy = schema.extend({})
    for field, field_type in copy.schema.items():
        if field.schema in defaults:
            field.default = vol.default_factory(defaults[field])
    return copy


@config_entries.HANDLERS.register(DOMAIN)
class FlowHandler(config_entries.ConfigFlow):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the Airbnk config flow."""
        self.host = None

    async def _create_entry(self, userId, email, token):
        """Register new entry."""
        # if not self.unique_id:
        #    await self.async_set_unique_id(password)
        # self._abort_if_unique_id_configured()
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        await self.async_set_unique_id("Airbnk_" + userId)

        return self.async_create_entry(
            title="Airbnk",
            data={CONF_EMAIL: email, CONF_TOKEN: token, CONF_USERID: userId},
        )

    async def _attempt_connection(self, email, token):
        """Create device."""
        res_json = await AirbnkApi.retrieveAccessToken(self.hass, email, token)
        if res_json is None:
            return self.async_abort(reason="token_retrieval_failed")

        _LOGGER.info("Token retrieval data: %s", res_json)

        userId = res_json["data"][CONF_USERID]
        token = res_json["data"][CONF_TOKEN]
        _LOGGER.debug("Done!: %s %s %s", userId, email, token)

        return await self._create_entry(userId, email, token)

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP1_SCHEMA)
        return await self.async_step_verify(user_input)

    async def async_step_verify(self, user_input=None):
        """Config flow: second step."""
        if user_input.get(CONF_CODE) is None:
            email = user_input.get(CONF_EMAIL)
            res = await AirbnkApi.requestVerificationCode(self.hass, email)
            if res is False:
                return self.async_abort(reason="code_request_failed")

            defaults = {}
            defaults.update(user_input or {})
            return self.async_show_form(
                step_id="verify", data_schema=schema_defaults(STEP2_SCHEMA, **defaults)
            )
        return await self._attempt_connection(
            user_input.get(CONF_EMAIL), user_input.get(CONF_CODE)
        )

    async def async_step_import(self, user_input):
        """Import a config entry from YAML."""
        _LOGGER.error("This integration does not support configuration via YAML file.")
