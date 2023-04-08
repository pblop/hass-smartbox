from copy import deepcopy
import logging
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.helpers import entity_registry
from custom_components.smartbox.const import (
    DOMAIN,
    CONF_ACCOUNTS,
    CONF_DEVICE_IDS,
    HEATER_NODE_TYPE_ACM,
    HEATER_NODE_TYPE_HTR,
    HEATER_NODE_TYPE_HTR_MOD,
)
from custom_components.smartbox.types import SetupDict, StatusDict

_LOGGER = logging.getLogger(__name__)


def mock_device(dev_id: str, nodes: List[MagicMock]) -> MagicMock:
    dev = MagicMock()
    dev.dev_id = dev_id
    dev.get_nodes = MagicMock(return_value=nodes)
    dev.initialise_nodes = AsyncMock()
    return dev


def mock_node(dev_id: str, addr: int, node_type: str, mode="auto") -> MagicMock:
    node = MagicMock()
    node.node_type = node_type
    node.name = f"node_{addr}"
    node.node_id = f"{dev_id}-{addr}"
    node.status = {
        "mtemp": "19.5",
        "units": "C",
        "sync_status": "ok",
        "locked": False,
        "power": "854",
        "mode": mode,
    }
    if node_type == HEATER_NODE_TYPE_ACM:
        node.status["charging"] = True
        node.status["charge_level"] = 4
    else:
        node.status["active"] = True
    if node_type == HEATER_NODE_TYPE_HTR:
        node.status["duty"] = 18
    if node_type == HEATER_NODE_TYPE_HTR_MOD:
        node.status["on"] = True
        node.status["selected_temp"] = "comfort"
        node.status["comfort_temp"] = "22"
        node.status["eco_offset"] = "2"
    else:
        node.status["stemp"] = "20"

    node.async_update = AsyncMock(return_value=node.status)
    return node


def get_climate_entity_name(mock_node: Dict[str, Any]) -> str:
    return mock_node["name"]


def get_sensor_entity_name(mock_node: Dict[str, Any], sensor_type: str) -> str:
    return f"{mock_node['name']} {sensor_type.capitalize()}"


def get_away_status_switch_entity_name(mock_device: Dict[str, Any]) -> str:
    return f"{mock_device['name']} Away Status"


def get_window_mode_switch_entity_name(mock_node: Dict[str, Any]) -> str:
    return f"{mock_node['name']} Window Mode"


def get_true_radiant_switch_entity_name(mock_node: Dict[str, Any]) -> str:
    return f"{mock_node['name']} True Radiant"


def get_power_limit_number_entity_name(mock_device: Dict[str, Any]) -> str:
    return f"{mock_device['name']} Power Limit"


def get_object_id(entity_name: str) -> str:
    return entity_name.lower().replace(" ", "_")


def get_entity_id_from_object_id(object_id: str, domain: str) -> str:
    return f"{domain}.{object_id}"


def get_climate_entity_id(mock_node: Dict[str, Any]) -> str:
    object_id = get_object_id(get_climate_entity_name(mock_node))
    return get_entity_id_from_object_id(object_id, CLIMATE_DOMAIN)


def get_sensor_entity_id(mock_node: Dict[str, Any], sensor_type: str) -> str:
    object_id = get_object_id(get_sensor_entity_name(mock_node, sensor_type))
    return get_entity_id_from_object_id(object_id, SENSOR_DOMAIN)


def get_away_status_switch_entity_id(mock_device: Dict[str, Any]) -> str:
    object_id = get_object_id(get_away_status_switch_entity_name(mock_device))
    return get_entity_id_from_object_id(object_id, SWITCH_DOMAIN)


def get_window_mode_switch_entity_id(mock_node: Dict[str, Any]) -> str:
    object_id = get_object_id(get_window_mode_switch_entity_name(mock_node))
    return get_entity_id_from_object_id(object_id, SWITCH_DOMAIN)


def get_true_radiant_switch_entity_id(mock_node: Dict[str, Any]) -> str:
    object_id = get_object_id(get_true_radiant_switch_entity_name(mock_node))
    return get_entity_id_from_object_id(object_id, SWITCH_DOMAIN)


def get_power_limit_number_entity_id(mock_device: Dict[str, Any]) -> str:
    object_id = get_object_id(get_power_limit_number_entity_name(mock_device))
    return get_entity_id_from_object_id(object_id, NUMBER_DOMAIN)


def get_device_unique_id(mock_device: Dict[str, Any], entity_type: str) -> str:
    return f"{mock_device['dev_id']}_{entity_type}"


def get_node_unique_id(
    mock_device: Dict[str, Any], mock_node: Dict[str, Any], entity_type: str
) -> str:
    return f"{mock_device['dev_id']}-{mock_node['addr']}_{entity_type}"


def get_entity_id_from_unique_id(hass, platform, unique_id):
    er = entity_registry.async_get(hass)
    entity_id = er.async_get_entity_id(platform, DOMAIN, unique_id)
    assert entity_id is not None
    return entity_id


class MockSmartbox(object):
    def __init__(
        self,
        mock_config,
        mock_device_info,
        mock_node_info,
        mock_node_setup: Dict[str, Dict[int, SetupDict]],
        mock_node_status: Dict[str, Dict[int, StatusDict]],
        start_available=True,
    ):
        self.config = mock_config
        assert len(mock_config[DOMAIN][CONF_ACCOUNTS]) == 1
        config_dev_ids = mock_config[DOMAIN][CONF_ACCOUNTS][0][CONF_DEVICE_IDS]
        self._device_info = mock_device_info
        self._devices = list(map(self._get_device, config_dev_ids))
        self._node_info = mock_node_info
        # socket has most up to date status/setup
        self._socket_node_setup = mock_node_setup
        self._session_node_setup = deepcopy(self._socket_node_setup)
        self._socket_node_status = mock_node_status
        if not start_available:
            for dev in self._devices:
                for node_info in self._node_info[dev["dev_id"]]:
                    self._socket_node_status[dev["dev_id"]][node_info["addr"]][
                        "sync_status"
                    ] = "lost"
        # session status can be stale
        self._session_node_status = deepcopy(self._socket_node_status)

        self._session = self._create_mock_session()
        self._sockets: Dict[str, MagicMock] = {}

    def _get_device(self, dev_id):
        return self._device_info[dev_id]

    def _create_mock_session(self):
        mock_session = MagicMock()
        mock_session.get_devices.return_value = self._devices

        def get_nodes(dev_id):
            return self._node_info[dev_id]

        mock_session.get_nodes.side_effect = get_nodes

        def get_status(dev_id, node):
            return self._get_session_status(dev_id, node["addr"])

        mock_session.get_status.side_effect = get_status

        def set_status(dev_id, node, status_updates):
            self._socket_node_status[dev_id][node["addr"]].update(status_updates)
            self._session_node_status = self._socket_node_status

        mock_session.set_status = set_status

        def get_setup(dev_id, node):
            return self._session_node_setup[dev_id][node["addr"]]

        mock_session.get_setup = get_setup

        def set_setup(dev_id, node, setup_updates):
            self._socket_node_setup[dev_id][node["addr"]].update(setup_updates)
            self._session_node_setup = self._socket_node_setup

        mock_session.set_setup = set_setup

        return mock_session

    def get_mock_session(
        self,
        api_name: str,
        basic_auth_credentials: str,
        username: str,
        password: str,
        retry_attempts: int,
        backoff_factor: float,
    ):
        """Patched to custom_components.smartbox.model.Session"""
        return self._session

    def _create_mock_socket(self, dev_id, on_dev_data, on_update):
        mock_socket = MagicMock()
        mock_socket.dev_id = dev_id
        mock_socket.on_dev_data = on_dev_data
        mock_socket.on_update = on_update
        mock_socket.run = AsyncMock()
        return mock_socket

    def get_mock_socket(
        self,
        session,
        dev_id,
        on_dev_data,
        on_update,
        reconnect_attempts,
        backoff_factor,
    ):
        """Patched to smartbox.update_manager.SocketSession"""
        assert session == self._session
        # shouldn't create more than one socket per device
        assert dev_id not in self._sockets
        mock_socket = self._create_mock_socket(dev_id, on_dev_data, on_update)
        self._sockets[dev_id] = mock_socket
        return mock_socket

    @property
    def session(self):
        return self._session

    def get_socket(self, dev_id: str):
        return self._sockets[dev_id]

    def get_devices(self):
        return self._devices

    def dev_data_update(self, mock_device, dev_data):
        socket = self._sockets[mock_device["dev_id"]]
        socket.on_dev_data(dev_data)

    def _get_session_status(self, dev_id: str, addr: int) -> StatusDict:
        status = self._session_node_status[dev_id][addr]
        if status["sync_status"] == "lost":
            return {"sync_status": "lost"}
        return status

    def _get_socket_status(self, dev_id: str, addr: int) -> StatusDict:
        status = self._socket_node_status[dev_id][addr]
        if status["sync_status"] == "lost":
            return {"sync_status": "lost"}
        return status

    def _get_socket_setup(self, dev_id: str, addr: int) -> SetupDict:
        return self._socket_node_setup[dev_id][addr]

    def generate_socket_status_update(
        self, mock_device, mock_node, status_updates: StatusDict
    ) -> StatusDict:
        dev_id = mock_device["dev_id"]
        addr = mock_node["addr"]
        self._socket_node_status[dev_id][addr].update(status_updates)
        self._send_socket_status_update(dev_id, addr)
        return self._get_socket_status(dev_id, addr)

    def generate_socket_setup_update(
        self, mock_device, mock_node, setup_updates: SetupDict
    ) -> SetupDict:
        dev_id = mock_device["dev_id"]
        addr = mock_node["addr"]
        self._socket_node_setup[dev_id][addr].update(setup_updates)
        self._send_socket_setup_update(dev_id, addr)
        return self._get_socket_setup(dev_id, addr)

    def generate_new_socket_status(self, mock_device, mock_node) -> StatusDict:
        dev_id = mock_device["dev_id"]
        addr = mock_node["addr"]
        status = self._socket_node_status[dev_id][addr]
        temp_increment = 0.1 if status["units"] == "C" else 1
        status["mtemp"] = str(float(status["mtemp"]) + temp_increment)
        if mock_node["type"] == HEATER_NODE_TYPE_HTR_MOD:
            status["comfort_temp"] = str(float(status["comfort_temp"]) + temp_increment)
        else:
            status["stemp"] = str(float(status["stemp"]) + temp_increment)
        # always set back to in-sync status
        status["sync_status"] = "ok"
        if mock_node["type"] != HEATER_NODE_TYPE_HTR_MOD:
            status["power"] = str(float(status["power"]) + 1)
        if mock_node["type"] == HEATER_NODE_TYPE_HTR:
            if status["active"]:
                status["duty"] = int(status["duty"]) + 1
                if int(status["duty"]) > 100:
                    # Duty is always 1 to 100 when active
                    status["duty"] = 1
            else:
                # If active is false duty is always 0
                status["duty"] = 0
        self._socket_node_status[dev_id][addr] = status

        self._send_socket_status_update(dev_id, addr)
        return self._get_socket_status(dev_id, addr)

    def generate_socket_node_unavailable(self, mock_device, mock_node) -> StatusDict:
        dev_id = mock_device["dev_id"]
        addr = mock_node["addr"]
        self._socket_node_status[dev_id][addr]["sync_status"] = "lost"
        self._send_socket_status_update(dev_id, addr)
        return self._get_socket_status(dev_id, addr)

    def _send_socket_status_update(self, dev_id: str, addr: int) -> None:
        socket = self._sockets[dev_id]
        node_type = self._node_info[dev_id][addr]["type"]
        socket.on_update(
            {
                "path": f"/{node_type}/{addr}/status",
                "body": self._get_socket_status(dev_id, addr),
            }
        )

    def _send_socket_setup_update(self, dev_id: str, addr: int) -> None:
        socket = self._sockets[dev_id]
        node_type = self._node_info[dev_id][addr]["type"]
        socket.on_update(
            {
                "path": f"/{node_type}/{addr}/setup",
                "body": self._get_socket_setup(dev_id, addr),
            }
        )


def active_or_charging_update(node_type: str, active: bool) -> StatusDict:
    if node_type == HEATER_NODE_TYPE_ACM:
        return {"charging": active}
    else:
        return {"active": active, "duty": 100 if active else 0}
