import logging
from unittest.mock import AsyncMock, MagicMock

from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT
from homeassistant.helpers import entity_registry
from homeassistant.util.unit_conversion import TemperatureConverter

from custom_components.smartbox.const import (
    DOMAIN,
    CONF_ACCOUNTS,
    CONF_DEVICE_IDS,
)

_LOGGER = logging.getLogger(__name__)


def mock_device(dev_id, nodes):
    dev = MagicMock()
    dev.dev_id = dev_id
    dev.get_nodes = MagicMock(return_value=nodes)
    dev.initialise_nodes = AsyncMock()
    return dev


def mock_node(dev_id, addr, node_type, mode="auto"):
    node = MagicMock()
    node.node_type = node_type
    node.name = f"node_{addr}"
    node.node_id = f"{dev_id}-{addr}"
    node.status = {
        "mtemp": "19.5",
        "stemp": "20",
        "units": "C",
        "sync_status": "ok",
        "locked": False,
        "active": True,
        "power": "854",
        "mode": mode,
    }
    node.async_update = AsyncMock(return_value=node.status)
    return node


def get_object_id(mock_node):
    return mock_node["name"].lower().replace(" ", "_")


def get_entity_id(mock_node, domain):
    object_id = get_object_id(mock_node)
    return f"{domain}.{object_id}"


def get_unique_id(mock_device, mock_node, device_type):
    return f"{mock_device['dev_id']}-{mock_node['addr']}_{device_type}"


def get_entity(hass, platform, unique_id):
    er = entity_registry.async_get(hass)
    entity_id = er.async_get_entity_id(platform, DOMAIN, unique_id)
    assert entity_id is not None
    return entity_id


class MockSmartbox(object):
    def __init__(
        self, mock_config, mock_node_info, mock_node_status, start_available=True
    ):
        self.config = mock_config
        assert len(mock_config[DOMAIN][CONF_ACCOUNTS]) == 1
        config_dev_ids = mock_config[DOMAIN][CONF_ACCOUNTS][0][CONF_DEVICE_IDS]
        self._devices = list(map(self._get_device, config_dev_ids))
        self._node_info = mock_node_info
        # socket has most up to date status
        self._socket_node_status = mock_node_status
        if not start_available:
            for dev in self._devices:
                for node_info in self._node_info[dev["dev_id"]]:
                    self._socket_node_status[dev["dev_id"]][node_info["addr"]][
                        "sync_status"
                    ] = "lost"
        # session status can be stale
        self._session_node_status = self._socket_node_status

        self.session = self._get_session()
        self.sockets = {}

    def _get_device(self, dev_id):
        return {
            "dev_id": dev_id,
        }

    def _get_session(self):
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

        return mock_session

    def get_mock_socket(
        self,
        session,
        dev_id,
        on_dev_data,
        on_update,
        reconnect_attempts,
        backoff_factor,
    ):
        assert session == self.session
        mock_socket = MagicMock()
        mock_socket.dev_id = dev_id
        mock_socket.on_dev_data = on_dev_data
        mock_socket.on_update = on_update
        mock_socket.run = AsyncMock()
        self.sockets[dev_id] = mock_socket
        return mock_socket

    def get_devices(self):
        return self._devices

    def dev_data_update(self, mock_device, dev_data):
        socket = self.sockets[mock_device["dev_id"]]
        socket.on_dev_data(dev_data)

    def _get_session_status(self, dev_id, addr):
        status = self._session_node_status[dev_id][addr]
        if status["sync_status"] == "lost":
            return {"sync_status": "lost"}
        return status

    def _get_socket_status(self, dev_id, addr):
        status = self._socket_node_status[dev_id][addr]
        if status["sync_status"] == "lost":
            return {"sync_status": "lost"}
        return status

    def generate_socket_status_update(self, mock_device, mock_node, status_updates):
        dev_id = mock_device["dev_id"]
        addr = mock_node["addr"]
        self._socket_node_status[dev_id][addr].update(status_updates)
        self._send_socket_update(dev_id, addr)
        return self._get_socket_status(dev_id, addr)

    def generate_new_socket_status(self, mock_device, mock_node):
        dev_id = mock_device["dev_id"]
        addr = mock_node["addr"]
        status = self._socket_node_status[dev_id][addr]
        temp_increment = 0.1 if status["units"] == "C" else 1
        status["mtemp"] = str(float(status["mtemp"]) + temp_increment)
        status["stemp"] = str(float(status["stemp"]) + temp_increment)
        # always set back to in-sync status
        status["sync_status"] = "ok"
        status["power"] = str(float(status["power"]) + 1)
        self._socket_node_status[dev_id][addr] = status

        self._send_socket_update(dev_id, addr)
        return self._get_socket_status(dev_id, addr)

    def generate_socket_node_unavailable(self, mock_device, mock_node):
        dev_id = mock_device["dev_id"]
        addr = mock_node["addr"]
        self._socket_node_status[dev_id][addr]["sync_status"] = "lost"
        self._send_socket_update(dev_id, addr)
        return self._get_socket_status(dev_id, addr)

    def _send_socket_update(self, dev_id, addr):
        socket = self.sockets[dev_id]
        node_type = self._node_info[dev_id][addr]["type"]
        socket.on_update(
            {
                "path": f"/{node_type}/{addr}/status",
                "body": self._get_socket_status(dev_id, addr),
            }
        )


def convert_temp(hass, node_units, temp):
    # Temperatures are converted to the units of the HA
    # instance, so do the same for comparison
    unit = TEMP_CELSIUS if node_units == "C" else TEMP_FAHRENHEIT
    return TemperatureConverter.convert(temp, unit, hass.config.units.temperature_unit)


def round_temp(hass, temp):
    print(f"TEMP {temp} {type(temp)}")
    # HA uses different precisions for Fahrenheit (whole
    # integers) vs Celsius (tenths)
    if hass.config.units.temperature_unit == TEMP_CELSIUS:
        return round(temp, 1)
    else:
        return round(temp)
