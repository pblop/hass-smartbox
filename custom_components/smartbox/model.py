import asyncio
import logging
import re

from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_HOME,
)
from homeassistant.core import HomeAssistant
from smartbox import Session, SocketSession
from typing import Any, Dict, List, Union
from unittest.mock import MagicMock

from .const import (
    GITHUB_ISSUES_URL,
    HEATER_NODE_TYPE_HTR_MOD,
    HEATER_NODE_TYPES,
)

_LOGGER = logging.getLogger(__name__)

_AWAY_STATUS_UPDATE_RE = re.compile(r"^/mgr/away_status")
_NODE_STATUS_UPDATE_RE = re.compile(r"^/([^/]+)/(\d+)/status")
_MESSAGE_SKIP_RE = re.compile(
    r"^/connected|/mgr/nodes|/([^/]+)/(\d+)/(prog|setup|version)"
)


class SmartboxDevice(object):
    def __init__(
        self,
        dev_id: str,
        session: Union[Session, MagicMock],
        socket_reconnect_attempts: int,
        socket_backoff_factor: float,
    ) -> None:
        self._dev_id = dev_id
        self._session = session
        self._socket_reconnect_attempts = socket_reconnect_attempts
        self._socket_backoff_factor = socket_backoff_factor

    async def initialise_nodes(self, hass: HomeAssistant) -> None:
        # Would do in __init__, but needs to be a coroutine
        session_nodes = await hass.async_add_executor_job(
            self._session.get_nodes, self.dev_id
        )
        self._nodes = {}
        for node_info in session_nodes:
            status = await hass.async_add_executor_job(
                self._session.get_status, self._dev_id, node_info
            )
            node = SmartboxNode(self, node_info, self._session, status)
            self._nodes[(node.node_type, node.addr)] = node

        _LOGGER.debug(f"Creating SocketSession for device {self._dev_id}")
        self._socket_session = SocketSession(
            self._session,
            self._dev_id,
            lambda data: self.on_dev_data(data),
            lambda data: self.on_update(data),
            reconnect_attempts=self._socket_reconnect_attempts,
            backoff_factor=self._socket_backoff_factor,
        )

        _LOGGER.debug(f"Starting SocketSession task for device {self._dev_id}")
        asyncio.create_task(self._socket_session.run())

    def on_dev_data(self, data: Dict[str, Dict[str, bool]]) -> None:
        _LOGGER.debug(f"Received dev_data: {data}")
        self._away_status_update(data["away_status"])

    def _away_status_update(self, away_status: Dict[str, bool]) -> None:
        _LOGGER.debug(f"Away status update: {away_status}")
        # update all nodes
        for node in self._nodes.values():
            node.away = away_status["away"]

    def _node_status_update(
        self, node_type: str, addr: int, node_status: Dict[str, Union[float, str, bool]]
    ) -> None:
        _LOGGER.debug(f"Node status update: {node_status}")
        node = self._nodes.get((node_type, addr), None)
        if node is not None:
            node.update_status(node_status)
        else:
            _LOGGER.error(f"Received update for unknown node {node_type} {addr}")

    def on_update(
        self,
        data: Dict[str, Any],
    ) -> None:
        _LOGGER.debug(f"Received update: {data}")

        m = _NODE_STATUS_UPDATE_RE.match(data["path"])
        if m:
            self._node_status_update(m.group(1), int(m.group(2)), data["body"])
            return

        m = _AWAY_STATUS_UPDATE_RE.match(data["path"])
        if m:
            self._away_status_update(data["body"])
            return

        m = _MESSAGE_SKIP_RE.match(data["path"])
        if m:
            _LOGGER.debug(f"Skipping update {data}")
            return

        _LOGGER.error(f"Couldn't match update {data}")

    @property
    def dev_id(self) -> str:
        return self._dev_id

    def get_nodes(self):
        return self._nodes.values()


class SmartboxNode(object):
    def __init__(
        self,
        device: Union[SmartboxDevice, MagicMock],
        node_info: Dict[str, Any],
        session: Union[Session, MagicMock],
        status: Dict[str, Any],
    ) -> None:
        self._device = device
        self._node_info = node_info
        self._session = session
        self._status = status
        self._away = False

    @property
    def node_id(self) -> str:
        # TODO: are addrs only unique among node types, or for the whole device?
        return f"{self._device.dev_id}-{self._node_info['addr']}"

    @property
    def name(self) -> str:
        return self._node_info["name"]

    @property
    def node_type(self) -> str:
        """Return node type, e.g. 'htr' for heaters"""
        return self._node_info["type"]

    @property
    def addr(self) -> int:
        return self._node_info["addr"]

    @property
    def status(self) -> Dict[str, Union[float, str, bool]]:
        return self._status

    def update_status(self, status: Dict[str, Union[float, str, bool]]) -> None:
        _LOGGER.debug(f"Updating node {self.name} status: {status}")
        self._status = status

    def set_status(self, **status_args) -> Dict[str, Union[float, str, bool]]:
        self._session.set_status(self._device.dev_id, self._node_info, status_args)
        # update our status locally until we get an update
        self._status |= {**status_args}
        return self._status

    @property
    def away(self):
        return self._away

    @away.setter
    def away(self, away):
        _LOGGER.debug(f"Updating node {self.name} away status: {away}")
        self._away = away

    async def async_update(
        self, hass: HomeAssistant
    ) -> Dict[str, Union[float, str, bool]]:
        return self.status


def is_heater_node(node: Union[SmartboxNode, MagicMock]) -> bool:
    return node.node_type in HEATER_NODE_TYPES


def is_supported_node(node: Union[SmartboxNode, MagicMock]) -> bool:
    # TODO: add support for 'thm' (thermostat) nodes
    return is_heater_node(node)


def get_temperature_unit(status):
    if "units" not in status:
        return None
    unit = status["units"]
    if unit == "C":
        return TEMP_CELSIUS
    elif unit == "F":
        return TEMP_FAHRENHEIT
    else:
        raise ValueError(f"Unknown temp unit {unit}")


async def get_devices(
    hass: HomeAssistant,
    api_name: str,
    basic_auth_creds: str,
    username: str,
    password: str,
    session_retry_attempts: int,
    session_backoff_factor: float,
    socket_reconnect_attempts: int,
    socket_backoff_factor: float,
) -> List[SmartboxDevice]:
    _LOGGER.info(
        f"Creating Smartbox session for {api_name}"
        f"(session_retry_attempts={session_retry_attempts}"
        f", session_backoff_factor={session_backoff_factor}"
        f", socket_reconnect_attempts={socket_reconnect_attempts}"
        f", socket_backoff_factor={session_backoff_factor})"
    )
    session = await hass.async_add_executor_job(
        Session,
        api_name,
        basic_auth_creds,
        username,
        password,
        session_retry_attempts,
        session_backoff_factor,
    )
    session_devices = await hass.async_add_executor_job(session.get_devices)
    # TODO: gather?
    devices = [
        await create_smartbox_device(
            hass,
            session_device["dev_id"],
            session,
            socket_reconnect_attempts,
            socket_backoff_factor,
        )
        for session_device in session_devices
    ]
    return devices


async def create_smartbox_device(
    hass: HomeAssistant,
    dev_id: str,
    session: Union[Session, MagicMock],
    socket_reconnect_attempts: int,
    socket_backoff_factor: float,
) -> Union[SmartboxDevice, MagicMock]:
    """Factory function for SmartboxDevices"""
    device = SmartboxDevice(
        dev_id, session, socket_reconnect_attempts, socket_backoff_factor
    )
    await device.initialise_nodes(hass)
    return device


def _check_status_key(key: str, node_type: str, status: Dict[str, Any]):
    if key not in status:
        raise KeyError(
            f"'{key}' not found in {node_type} - please report to {GITHUB_ISSUES_URL}. "
            f"status: {status}"
        )


def get_target_temperature(node_type: str, status: Dict[str, Any]) -> float:
    if node_type == HEATER_NODE_TYPE_HTR_MOD:
        _check_status_key("selected_temp", node_type, status)
        if status["selected_temp"] == "comfort":
            _check_status_key("comfort_temp", node_type, status)
            return float(status["comfort_temp"])
        elif status["selected_temp"] == "eco":
            _check_status_key("comfort_temp", node_type, status)
            _check_status_key("eco_offset", node_type, status)
            return float(status["comfort_temp"]) - float(status["eco_offset"])
        elif status["selected_temp"] == "ice":
            _check_status_key("ice_temp", node_type, status)
            return float(status["ice_temp"])
        else:
            raise KeyError(
                f"'Unexpected 'selected_temp' value {status['selected_temp']} found for "
                f"{node_type} - please report to {GITHUB_ISSUES_URL}. status: {status}"
            )
    else:
        _check_status_key("stemp", node_type, status)
        return float(status["stemp"])


def set_temperature_args(
    node_type: str, status: Dict[str, Any], temp: float
) -> Dict[str, Any]:
    _check_status_key("units", node_type, status)
    if node_type == HEATER_NODE_TYPE_HTR_MOD:
        if status["selected_temp"] == "comfort":
            target_temp = temp
        elif status["selected_temp"] == "eco":
            _check_status_key("eco_offset", node_type, status)
            target_temp = temp + float(status["eco_offset"])
        elif status["selected_temp"] == "ice":
            raise ValueError(
                "Can't set temperature for htr_mod devices when ice mode is selected"
            )
        else:
            raise KeyError(
                f"'Unexpected 'selected_temp' value {status['selected_temp']} found for "
                f"{node_type} - please report to {GITHUB_ISSUES_URL}. status: {status}"
            )
        return {
            "on": True,
            "mode": status["mode"],
            "selected_temp": status["selected_temp"],
            "comfort_temp": str(target_temp),
            "eco_offset": status["eco_offset"],
            "units": status["units"],
        }
    else:
        return {
            "stemp": str(temp),
            "units": status["units"],
        }


def get_hvac_mode(node_type: str, status: Dict[str, Any]) -> str:
    _check_status_key("mode", node_type, status)
    if status["mode"] == "off":
        return HVAC_MODE_OFF
    elif node_type == HEATER_NODE_TYPE_HTR_MOD and not status["on"]:
        return HVAC_MODE_OFF
    elif status["mode"] == "manual":
        return HVAC_MODE_HEAT
    elif status["mode"] == "auto":
        return HVAC_MODE_AUTO
    elif status["mode"] == "modified_auto":
        # This occurs when the temperature is modified while in auto mode.
        # Mapping it to auto seems to make this most sense
        return HVAC_MODE_AUTO
    elif status["mode"] == "self_learn":
        return HVAC_MODE_AUTO
    elif status["mode"] == "presence":
        return HVAC_MODE_AUTO
    else:
        _LOGGER.error(f"Unknown smartbox node mode {status['mode']}")
        raise ValueError(f"Unknown smartbox node mode {status['mode']}")


def set_hvac_mode_args(
    node_type: str, status: Dict[str, Any], hvac_mode: str
) -> Dict[str, Any]:
    if node_type == HEATER_NODE_TYPE_HTR_MOD:
        if hvac_mode == HVAC_MODE_OFF:
            return {"on": False}
        elif hvac_mode == HVAC_MODE_HEAT:
            # We need to pass these status keys on when setting the mode
            required_status_keys = ["selected_temp"]
            for key in required_status_keys:
                _check_status_key(key, node_type, status)
            hvac_mode_args = {k: status[k] for k in required_status_keys}
            hvac_mode_args["on"] = True
            hvac_mode_args["mode"] = "manual"
            return hvac_mode_args
        elif hvac_mode == HVAC_MODE_AUTO:
            # TODO: differentiate other modes we consider 'auto' (self_learn
            # and presence)
            return {"on": True, "mode": "auto"}
        else:
            raise ValueError(f"Unsupported hvac mode {hvac_mode}")
    else:
        if hvac_mode == HVAC_MODE_OFF:
            return {"mode": "off"}
        elif hvac_mode == HVAC_MODE_HEAT:
            return {"mode": "manual"}
        elif hvac_mode == HVAC_MODE_AUTO:
            return {"mode": "auto"}
        else:
            raise ValueError(f"Unsupported hvac mode {hvac_mode}")


def get_preset_mode(node_type: str, away: bool) -> str:
    if away:
        return PRESET_AWAY
    return PRESET_HOME


def get_preset_modes(node_type: str) -> List[str]:
    return [PRESET_AWAY, PRESET_HOME]
