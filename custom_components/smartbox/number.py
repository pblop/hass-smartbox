from homeassistant.components.number import (
    NumberEntity,
)
from homeassistant.core import HomeAssistant
import logging
from typing import Any, Callable, Dict, Optional, Union
from unittest.mock import MagicMock

from .const import DOMAIN, SMARTBOX_DEVICES
from .model import SmartboxDevice

_LOGGER = logging.getLogger(__name__)
_MAX_POWER_LIMIT = 9999


async def async_setup_platform(
    hass: HomeAssistant,
    config: Dict[Any, Any],
    async_add_entities: Callable,
    discovery_info: Optional[Dict[Any, Any]] = None,
) -> None:
    """Set up platform."""
    _LOGGER.debug("Setting up Smartbox number platform")
    if discovery_info is None:
        return

    async_add_entities(
        [DevicePowerLimit(device) for device in hass.data[DOMAIN][SMARTBOX_DEVICES]],
        True,
    )

    _LOGGER.debug("Finished setting up Smartbox number platform")


class DevicePowerLimit(NumberEntity):
    """Smartbox device power limit"""

    def __init__(self, device: Union[SmartboxDevice, MagicMock]) -> None:
        self._device = device

    native_max_value: float = _MAX_POWER_LIMIT

    @property
    def name(self):
        """Return the name of the number."""
        return f"{self._device.name} Power Limit"

    @property
    def unique_id(self) -> str:
        return f"{self._device.dev_id}_power_limit"

    @property
    def native_value(self) -> float:
        return self._device.power_limit

    def set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._device.set_power_limit(int(value))
