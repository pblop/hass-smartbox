from homeassistant.components.switch import (
    SwitchEntity,
)
from homeassistant.core import HomeAssistant
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from unittest.mock import MagicMock

from .const import DOMAIN, SMARTBOX_DEVICES, SMARTBOX_NODES
from .model import SmartboxDevice, SmartboxNode, window_mode_available

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

    switch_entities: List[SwitchEntity] = []
    for device in hass.data[DOMAIN][SMARTBOX_DEVICES]:
        _LOGGER.debug("Creating away switch for device %s", device.name)
        switch_entities.append(AwaySwitch(device))

    for node in hass.data[DOMAIN][SMARTBOX_NODES]:
        if window_mode_available(node):
            _LOGGER.debug("Creating window_mode switch for node %s", node.name)
            switch_entities.append(WindowModeSwitch(node))
        else:
            _LOGGER.info("Window mode not available for node %s", node.name)

    async_add_entities(switch_entities, True)

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


class WindowModeSwitch(SwitchEntity):
    """Smartbox node window mode switch"""

    def __init__(self, node: Union[SmartboxNode, MagicMock]) -> None:
        self._node = node

    @property
    def name(self):
        """Return the name of the switch."""
        return f"{self._node.name} Window Mode"

    @property
    def unique_id(self) -> str:
        return f"{self._node.node_id}_window_mode"

    def turn_on(self, **kwargs):  # pylint: disable=unused-argument
        """Turn on the switch."""
        return self._node.set_window_mode(True)

    def turn_off(self, **kwargs):  # pylint: disable=unused-argument
        """Turn off the switch."""
        return self._node.set_window_mode(False)

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._node.window_mode
