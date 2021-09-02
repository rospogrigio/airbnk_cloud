"""Support for Airbnk locks."""
import logging
import asyncio
from time import sleep

from homeassistant.components.cover import (
    DOMAIN,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    CoverEntity,
)

from .const import DOMAIN as AIRBNK_DOMAIN, AIRBNK_API, AIRBNK_DEVICES

_LOGGER = logging.getLogger(__name__)

LOCK_ICON = "hass:door-closed-lock"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the platform.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Airbnk climate based on config_entry."""
    locks = []
    for dev_id, device in hass.data[AIRBNK_DOMAIN][AIRBNK_DEVICES].items():
        lock = AirbnkLock(hass.data[AIRBNK_DOMAIN][AIRBNK_API], device, dev_id)
        locks.append(lock)
    async_add_entities(locks)


class AirbnkLock(CoverEntity):
    """Representation of a lock."""

    def __init__(self, api, device, lock_id: str):
        """Initialize the zone."""
        self._api = api
        self._device = device
        self._lock_id = lock_id
        deviceName = self._device["deviceName"]
        self._name = f"{deviceName}"

    @property
    def supported_features(self):
        """Flag supported features."""
        supported_features = SUPPORT_OPEN | SUPPORT_CLOSE
        return supported_features

    @property
    def unique_id(self):
        """Return a unique ID."""
        devID = self._device["sn"]
        return f"{devID}"

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return LOCK_ICON

    @property
    def name(self):
        """Return the name of the lock."""
        return self._name

    @property
    def device_info(self):
        """Return a device description for device registry."""
        devID = self._device["sn"]
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, devID)
            },
            "manufacturer": "Airbnk",
            "model": self._device["deviceType"],
            "name": self._device["deviceName"],
            "sw_version": self._device["firmwareVersion"],
        }

    @property
    def is_opening(self):
        """Return if cover is opening."""
        return False

    @property
    def is_closing(self):
        """Return if cover is closing."""
        return False

    @property
    def is_open(self):
        """Return if the cover is open or not."""
        return None

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        return None

    async def async_stop_after_timeout(self, delay_sec):
        """Stop the cover if timeout (max movement span) occurred."""
        await asyncio.sleep(delay_sec)
        _LOGGER.debug("FATTP!")
        raise Exception("FATTO!")

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        _LOGGER.debug("Launching command to open")
        res = "await self._api.operateLock(self._device['sn'], True)"
        sleep(10)
        _LOGGER.debug("res: %s", res)
        self.hass.async_create_task(self.async_stop_after_timeout(2))

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        _LOGGER.debug("Launching command to close")
        res = "await self._api.operateLock(self._device['sn'], False)"
        sleep(2)
        _LOGGER.debug("res: %s", res)
        self.hass.bus.fire("Airbnk", {"wow": "from a Python script!"})

        self.hass.async_create_task(self.async_stop_after_timeout(2))

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        _LOGGER.debug("Launching command to stop")

    async def async_update(self):
        """Retrieve latest state."""
        # _LOGGER.debug("async_update")
