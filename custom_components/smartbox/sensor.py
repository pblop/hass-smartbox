from homeassistant.const import (
    ATTR_LOCKED,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_POWER,
    PERCENTAGE,
    POWER_WATT,
)
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
import logging
from typing import Any, Callable, Dict, Optional, Union
from unittest.mock import MagicMock

from .const import (
    DOMAIN,
    HEATER_NODE_TYPE_ACM,
    HEATER_NODE_TYPE_HTR_MOD,
    SMARTBOX_NODES,
)
from .model import get_temperature_unit, is_heater_node, is_heating, SmartboxNode

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

    # Temperature
    async_add_entities(
        [
            TemperatureSensor(node)
            for node in hass.data[DOMAIN][SMARTBOX_NODES]
            if is_heater_node(node)
        ],
        True,
    )
    # Power
    async_add_entities(
        [
            PowerSensor(node)
            for node in hass.data[DOMAIN][SMARTBOX_NODES]
            if is_heater_node(node) and node.node_type != HEATER_NODE_TYPE_HTR_MOD
        ],
        True,
    )
    # Charge Level
    async_add_entities(
        [
            ChargeLevelSensor(node)
            for node in hass.data[DOMAIN][SMARTBOX_NODES]
            if is_heater_node(node) and node.node_type == HEATER_NODE_TYPE_ACM
        ],
        True,
    )

    _LOGGER.debug("Finished setting up Smartbox sensor platform")


class SmartboxSensorBase(SensorEntity):
    def __init__(self, node: Union[SmartboxNode, MagicMock]) -> None:
        self._node = node
        self._status: Dict[str, Any] = {}
        self._available = False  # unavailable until we get an update
        _LOGGER.debug(f"Created node {self.name} unique_id={self.unique_id}")

    @property
    def extra_state_attributes(self) -> Dict[str, bool]:
        return {
            ATTR_LOCKED: self._status["locked"],
        }

    @property
    def available(self) -> bool:
        return self._available

    async def async_update(self) -> None:
        new_status = await self._node.async_update(self.hass)
        if new_status["sync_status"] == "ok":
            # update our status
            self._status = new_status
            self._available = True
        else:
            self._available = False


class TemperatureSensor(SmartboxSensorBase):
    """Smartbox heater temperature sensor"""

    device_class = DEVICE_CLASS_TEMPERATURE
    state_class = SensorStateClass.MEASUREMENT

    def __init__(self, node: Union[SmartboxNode, MagicMock]) -> None:
        super().__init__(node)

    @property
    def name(self) -> str:
        return f"{self._node.name} Temperature"

    @property
    def unique_id(self) -> str:
        return f"{self._node.node_id}_temperature"

    @property
    def native_value(self) -> float:
        return self._status["mtemp"]

    @property
    def native_unit_of_measurement(self) -> str:
        return get_temperature_unit(self._status)


class PowerSensor(SmartboxSensorBase):
    """Smartbox heater power sensor"""

    device_class = DEVICE_CLASS_POWER
    native_unit_of_measurement = POWER_WATT
    state_class = SensorStateClass.MEASUREMENT

    def __init__(self, node: Union[SmartboxNode, MagicMock]) -> None:
        super().__init__(node)

    @property
    def name(self) -> str:
        return f"{self._node.name} Power"

    @property
    def unique_id(self) -> str:
        return f"{self._node.node_id}_power"

    @property
    def native_value(self) -> float:
        # TODO: is this correct? The heater seems to report power usage all the
        # time otherwise, which doesn't make sense and doesn't tally with the
        # graphs in the vendor app UI
        return (
            self._status["power"]
            if is_heating(self._node.node_type, self._status)
            else 0
        )


class ChargeLevelSensor(SmartboxSensorBase):
    """Smartbox storage heater charge level sensor"""

    device_class = DEVICE_CLASS_BATTERY
    native_unit_of_measurement = PERCENTAGE
    state_class = SensorStateClass.MEASUREMENT

    def __init__(self, node: Union[SmartboxNode, MagicMock]) -> None:
        super().__init__(node)

    @property
    def name(self) -> str:
        return f"{self._node.name} Charge Level"

    @property
    def unique_id(self) -> str:
        return f"{self._node.node_id}_charge_level"

    @property
    def native_value(self) -> int:
        return self._status["charge_level"]
