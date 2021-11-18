"""Support for Airbnk sensors."""
import logging

from homeassistant.helpers.entity import Entity

from .const import DOMAIN as AIRBNK_DOMAIN, AIRBNK_API, AIRBNK_DEVICES, CONF_LOCKSTATUS

_LOGGER = logging.getLogger(__name__)

SENSOR_ICON = "hass:post-outline"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the platform.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Airbnk sensors based on config_entry."""
    sensors = []
    for dev_id, device in hass.data[AIRBNK_DOMAIN][AIRBNK_DEVICES].items():
        sensor = AirbnkSensor(hass.data[AIRBNK_DOMAIN][AIRBNK_API], device, dev_id)
        sensors.append(sensor)
    async_add_entities(sensors)


class AirbnkSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, api, device, sensor_id: str):
        """Initialize the zone."""
        self._api = api
        self._device = device
        self._sensor_id = sensor_id
        deviceName = self._device["deviceName"]
        self._name = f"{deviceName} status"

    @property
    def unique_id(self):
        """Return a unique ID."""
        devID = self._device["sn"]
        return f"{devID}_status"

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return SENSOR_ICON

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_info(self):
        """Return a device description for device registry."""
        devID = self._device["sn"]
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (AIRBNK_DOMAIN, devID)
            },
            "manufacturer": "Airbnk",
            "model": self._device["deviceType"],
            "name": self._device["deviceName"],
            "sw_version": self._device["firmwareVersion"],
        }

    @property
    def state(self):
        status = self._api.devices[self._sensor_id][CONF_LOCKSTATUS]
        return status

    async def async_update(self):
        """Retrieve latest state."""
        # _LOGGER.debug("async_update")
