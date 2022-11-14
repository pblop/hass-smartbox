from homeassistant.components.switch import (
    SwitchEntity,
)
from homeassistant.core import HomeAssistant
import logging
from typing import Any, Callable, Dict, Optional, Union
from unittest.mock import MagicMock

from .const import DOMAIN, SMARTBOX_DEVICES
from .model import SmartboxDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: Dict[Any, Any],
    async_add_entities: Callable,
    discovery_info: Optional[Dict[Any, Any]] = None,
) -> None:
    """Set up platform."""
    _LOGGER.debug("Setting up Smartbox switch platform")
    if discovery_info is None:
        return

    async_add_entities(
        [AwaySwitch(device) for device in hass.data[DOMAIN][SMARTBOX_DEVICES]],
        True,
    )

    _LOGGER.debug("Finished setting up Smartbox switch platform")


class AwaySwitch(SwitchEntity):
    """Smartbox device away switch"""

    def __init__(self, device: Union[SmartboxDevice, MagicMock]) -> None:
        self._device = device

    @property
    def name(self):
        """Return the name of the switch."""
        return f"{self._device.name} Away Status"

    @property
    def unique_id(self) -> str:
        return f"{self._device.dev_id}_away_status"

    def turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the switch."""
        return self._device.set_away_status(True)

    def turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the switch."""
        return self._device.set_away_status(False)

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._device.away
