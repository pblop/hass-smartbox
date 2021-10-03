import logging

from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_POWER,
    POWER_WATT,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.helpers.entity import Entity
from homeassistant.const import ATTR_LOCKED

from .const import DOMAIN, SMARTBOX_NODES
from .model import is_heater_node
from custom_components.smartbox.model import SmartboxNode
from homeassistant.core import HomeAssistant
from typing import Any, Callable, Dict, Optional, Union
from unittest.mock import MagicMock

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: Dict[Any, Any],
    async_add_entities: Callable,
    discovery_info: Optional[Dict[Any, Any]] = None,
) -> None:
    """Set up platform."""
    _LOGGER.debug("Setting up Smartbox sensor platform")
    if discovery_info is None:
        return

    async_add_entities(
        [
            TemperatureSensor(node)
            for node in hass.data[DOMAIN][SMARTBOX_NODES]
            if is_heater_node(node)
        ],
        True,
    )
    async_add_entities(
        [
            PowerSensor(node)
            for node in hass.data[DOMAIN][SMARTBOX_NODES]
            if is_heater_node(node)
        ],
        True,
    )

    _LOGGER.debug("Finished setting up Smartbox sensor platform")


class SmartboxSensorBase(Entity):
    def __init__(self, node: Union[SmartboxNode, MagicMock]) -> None:
        self._node = node
        self._status: Dict[str, Any] = {}
        self._available = False  # unavailable until we get an update
        _LOGGER.debug(f"Created node {self.name} unique_id={self.unique_id}")

    @property
    def name(self) -> str:
        return self._node.name

    @property
    def device_state_attributes(self) -> Dict[str, bool]:
        return {
            ATTR_LOCKED: self._status["locked"],
        }

    @property
    def available(self) -> bool:
        return self._available

    async def async_update(self) -> None:
        _LOGGER.debug("Smartbox sensor async_update")
        await self._node.async_update(self.hass)
        new_status = self._node.status
        if new_status["sync_status"] == "ok":
            # update our status
            self._status = new_status
            self._available = True
        else:
            self._available = False


class TemperatureSensor(SmartboxSensorBase):
    """Smartbox heater temperature sensor"""

    device_class = DEVICE_CLASS_TEMPERATURE

    def __init__(self, node: Union[SmartboxNode, MagicMock]) -> None:
        super().__init__(node)

    @property
    def unique_id(self) -> str:
        return f"{self._node.node_id}_temperature"

    @property
    def state(self) -> float:
        return self._status["mtemp"]

    @property
    def unit_of_measurement(self) -> str:
        return TEMP_CELSIUS if self._status["units"] == "C" else TEMP_FAHRENHEIT


class PowerSensor(SmartboxSensorBase):
    """Smartbox heater power sensor"""

    device_class = DEVICE_CLASS_POWER

    def __init__(self, node: Union[SmartboxNode, MagicMock]) -> None:
        super().__init__(node)

    @property
    def unique_id(self) -> str:
        return f"{self._node.node_id}_power"

    @property
    def state(self) -> Union[float, int]:
        # TODO: is this correct? The heater seems to report power usage all the
        # time otherwise, which doesn't make sense and doesn't tally with the
        # graphs in the vendor app UI
        return self._status["power"] if self._status["active"] else 0

    @property
    def unit_of_measurement(self) -> str:
        return POWER_WATT
