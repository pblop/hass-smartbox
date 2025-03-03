from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.climate.const import (
    PRESET_AWAY,
    PRESET_HOME,
)
from homeassistant.const import (
    ATTR_LOCKED,
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from unittest.mock import MagicMock

from .const import (
    DOMAIN,
    HEATER_NODE_TYPE_HTR_MOD,
    SMARTBOX_NODES,
)
from .model import (
    get_hvac_mode,
    get_preset_mode,
    get_preset_modes,
    get_target_temperature,
    get_temperature_unit,
    is_heater_node,
    is_heating,
    set_hvac_mode_args,
    set_preset_mode_status_update,
    set_temperature_args,
    SmartboxNode,
)
from .types import StatusDict

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: Dict[Any, Any],
    async_add_entities: Callable,
    discovery_info: Optional[Dict[Any, Any]] = None,
) -> None:
    """Set up platform."""
    _LOGGER.debug("Setting up Smartbox climate platform")
    if discovery_info is None:
        return

    async_add_entities(
        [
            SmartboxHeater(node)
            for node in hass.data[DOMAIN][SMARTBOX_NODES]
            if is_heater_node(node)
        ],
        True,
    )
    _LOGGER.debug("Finished setting up Smartbox climate platform")


def status_to_hvac_action(node_type: str, status: StatusDict) -> str:
    return HVACAction.HEATING if is_heating(node_type, status) else HVACAction.IDLE


class SmartboxHeater(ClimateEntity):
    """Smartbox heater climate control"""

    def __init__(self, node: Union[MagicMock, SmartboxNode]) -> None:
        """Initialize the sensor."""
        self._node = node
        self._status: Dict[str, Any] = {}
        self._available = False  # unavailable until we get an update
        self._supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )
        _LOGGER.debug(f"Created node {self.name} unique_id={self.unique_id}")

    @property
    def unique_id(self) -> str:
        """Return Unique ID string."""
        return f"{self._node.node_id}_climate"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._node.name

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return self._supported_features

    @property
    def should_poll(self) -> bool:
        """Return the polling state."""
        return True

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        unit = get_temperature_unit(self._status)
        if unit is not None:
            return unit
        else:
            return (
                TEMP_CELSIUS  # climate sensors need a temperature unit on construction
            )

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return float(self._status["mtemp"])

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        return get_target_temperature(self._node.node_type, self._status)

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            status_args = set_temperature_args(self._node.node_type, self._status, temp)
            self._node.set_status(**status_args)

    @property
    def hvac_action(self) -> str:
        """Return current operation ie. heat or idle."""
        action = status_to_hvac_action(self._node.node_type, self._status)
        return action

    @property
    def hvac_mode(self) -> str:
        """Return hvac target hvac state."""
        hvac_mode = get_hvac_mode(self._node.node_type, self._status)
        return hvac_mode

    @property
    def hvac_modes(self) -> List[str]:
        """Return the list of available operation modes."""
        hvac_modes = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
        return hvac_modes

    def set_hvac_mode(self, hvac_mode):
        """Set operation mode."""
        _LOGGER.debug(f"Setting HVAC mode to {hvac_mode}")
        status_args = set_hvac_mode_args(self._node.node_type, self._status, hvac_mode)
        self._node.set_status(**status_args)

    @property
    def preset_mode(self) -> str:
        return get_preset_mode(self._node.node_type, self._status, self._node.away)

    @property
    def preset_modes(self) -> List[str]:
        return get_preset_modes(self._node.node_type)

    def set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == PRESET_AWAY:
            self._node.update_device_away_status(True)
            return
        if self._node.away:
            self._node.update_device_away_status(False)
        if self._node.node_type == HEATER_NODE_TYPE_HTR_MOD:
            status_update = set_preset_mode_status_update(
                self._node.node_type, self._status, preset_mode
            )
            self._node.set_status(**status_update)
        elif preset_mode != PRESET_HOME:
            raise ValueError(
                f"Unsupported preset_mode {preset_mode} for {self._node.node_type} node"
            )

    @property
    def extra_state_attributes(self) -> Dict[str, bool]:
        """Return the state attributes of the device."""
        return {
            ATTR_LOCKED: self._status["locked"],
        }

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return self._available

    async def async_update(self) -> None:
        new_status = await self._node.async_update(self.hass)
        if new_status["sync_status"] == "ok":
            # update our status
            self._status = new_status
            self._available = True
        else:
            self._available = False
