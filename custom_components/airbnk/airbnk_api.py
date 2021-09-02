"""Platform for the Airbnk AC."""
import datetime
import functools
import logging
import requests
import uuid

from homeassistant.util import Throttle
from homeassistant.const import CONF_TOKEN

from .const import DOMAIN, AIRBNK_DEVICES, CONF_USERID

_LOGGER = logging.getLogger(__name__)

AIRBNK_CLOUD_URL = "https://wehereapi.seamooncloud.com"
AIRBNK_LANGUAGE = "2"
AIRBNK_VERSION = "A_FD_1.8.0"
MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(seconds=15)

AIRBNK_HEADERS = {
    "user-agent": "okhttp/3.12.0",
    "Accept-Encoding": "gzip, deflate",
}


class AirbnkApi:
    """Airbnk API."""

    def __init__(self, hass, entry):
        """Initialize a new Airbnk API."""
        _LOGGER.info("Initialing Airbnk API...")
        self.hass = hass
        self._config_entry = entry
        self.token = None
        self.devices = {}

        _LOGGER.debug("Initialing Airbnk API (%s)", entry.data[CONF_TOKEN])

        # if entry is not None:
        #     self.token = entry.data[CONF_TOKEN].copy()

        _LOGGER.info("Airbnk API initialized.")

    @staticmethod
    async def requestVerificationCode(hass, email):
        """Attempt to refresh the Access Token."""
        url = AIRBNK_CLOUD_URL + "/api/lock/sms?loginAcct=" + email
        url += "&language=" + AIRBNK_LANGUAGE + "&version=" + AIRBNK_VERSION
        url += "&mark=10&userId="

        try:
            func = functools.partial(requests.post, url, headers=AIRBNK_HEADERS)
            res = await hass.async_add_executor_job(func)
        except Exception as e:
            _LOGGER.error("CALL FAILED: %s", e)

        if res.status_code != 200:
            _LOGGER.error(
                "Verification code request failed (%s): %s",
                res.status_code, res.text
            )
            return False

        _LOGGER.info("Verification code request succeeded.")
        return True

    @staticmethod
    async def retrieveAccessToken(hass, email, code):
        _LOGGER.info("Retrieving new Token...")
        url = AIRBNK_CLOUD_URL + "/api/lock/loginByAuthcode?loginAcct=" + email
        url += "&authCode=" + code + "&systemCode=Android"
        url += "&language=" + AIRBNK_LANGUAGE + "&version=" + AIRBNK_VERSION
        url += "&deviceID=123456789012345&mark=1"
        _LOGGER.info("Retrieving: %s", url)

        try:
            func = functools.partial(requests.get, url, headers=AIRBNK_HEADERS)
            res = await hass.async_add_executor_job(func)
        except Exception as e:
            _LOGGER.error("CALL FAILED: %s", e)

        if res.status_code != 200:
            _LOGGER.error("Token retrieval failed (%s): %s", res.status_code, res.text)
            return None

        res_json = res.json()

        if res_json["code"] != 200:
            _LOGGER.error(
                "Token retrieval failed2 (%s): %s",
                res_json["code"], res.text
            )
            return None

        _LOGGER.info("Token retrieval succeeded.")
        return res_json

    async def operateLock(self, lockSN, isOpen):
        """Get pure Device Data from the Airbnk cloud devices."""
        _LOGGER.debug("operateLock %s %s.", lockSN, isOpen)
        token = self._config_entry.data[CONF_TOKEN]
        userId = self._config_entry.data[CONF_USERID]
        uuid_str = str(uuid.uuid4())
        mark = '2' if isOpen else '1'
        gatewaySn = self.devices[lockSN]['gateway']

        url = AIRBNK_CLOUD_URL + "/api/lock/lockOrUnlockChildDevice"
        url += "?language=" + AIRBNK_LANGUAGE + "&sn=" + gatewaySn
        url += "&userId=" + userId + "&uuid=" + uuid_str + "&version=" + AIRBNK_VERSION
        url += "&mark=" + mark + "&childDeviceSn=" + lockSN + "&token=" + token
        _LOGGER.info("operateLock url %s.", url)

        try:
            func = functools.partial(requests.post, url, headers=AIRBNK_HEADERS)
            res = await self.hass.async_add_executor_job(func)
        except Exception as e:
            _LOGGER.error("CALL FAILED: %s", e)
            return "CALL FAILED"

        if res.status_code != 200:
            _LOGGER.error("operateLock failed (%s): %s", res.status_code, res.text)
            return "operateLock failed : " + str(res.status_code)

        json_data = res.json()
        if json_data["code"] != 200:
            _LOGGER.error("operateLock failed2 (%s): %s", json_data["code"], res.text)
            msg = "FAILED: " + json_data["info"] + " (" + str(json_data["code"]) + ")"
            _LOGGER.error("%s", msg)
            return msg

        _LOGGER.info("operateLock request succeeded: %s", res.text)
        return ""

    async def getCloudDevices(self):
        """Get array of AirbnkResidentialDevice objects and get their data."""
        _LOGGER.info("getCloudDevices.")
        userId = self._config_entry.data[CONF_USERID]
        token = self._config_entry.data[CONF_TOKEN]

        url = AIRBNK_CLOUD_URL + "/api/v2/lock/getAllDevicesNew"
        url += "?language=" + AIRBNK_LANGUAGE + "&userId=" + userId
        url += "&version=" + AIRBNK_VERSION + "&token=" + token
        _LOGGER.info("Retrieving: %s", url)

        try:
            func = functools.partial(requests.get, url, headers=AIRBNK_HEADERS)
            res = await self.hass.async_add_executor_job(func)
        except Exception as e:
            _LOGGER.error("GCD CALL FAILED: %s", e)

        if res.status_code != 200:
            _LOGGER.error("GCD failed (%s): %s", res.status_code, res.text)
            return None

        json_data = res.json()
        if json_data["code"] != 200:
            _LOGGER.error("GCD failed2 (%s): %s", json_data["code"], res.text)
            return None

        _LOGGER.info("Token retrieval succeeded (%s): %s", res.status_code, res.text)
        _LOGGER.info("Token retrieval succeeded.")

        res = {}
        for dev_data in json_data["data"] or []:
            if dev_data["gateway"] == "":
                _LOGGER.info("Device '%s' is filtered out", dev_data["deviceName"])
            else:
                res[dev_data["sn"]] = dev_data["deviceName"]
                self.devices[dev_data["sn"]] = dev_data
        _LOGGER.info("Returning res %s", res)
        return self.devices

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs):
        """Pull the latest data from Airbnk."""
        _LOGGER.debug("API UPDATE")

        json_data = await self.getCloudDeviceDetails()
        for dev_data in json_data or []:
            if dev_data["id"] in self.hass.data[DOMAIN][AIRBNK_DEVICES]:
                self.hass.data[DOMAIN][AIRBNK_DEVICES][dev_data["id"]].setJsonData(
                    dev_data
                )
