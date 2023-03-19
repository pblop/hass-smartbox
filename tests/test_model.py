import logging
import pytest
from unittest.mock import (
    MagicMock,
    NonCallableMock,
    patch,
)

from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_ACTIVITY,
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_HOME,
)
from custom_components.smartbox.const import (
    DOMAIN,
    CONF_ACCOUNTS,
    CONF_API_NAME,
    CONF_BASIC_AUTH_CREDS,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_SESSION_RETRY_ATTEMPTS,
    CONF_SESSION_BACKOFF_FACTOR,
    CONF_SOCKET_RECONNECT_ATTEMPTS,
    CONF_SOCKET_BACKOFF_FACTOR,
    HEATER_NODE_TYPE_ACM,
    HEATER_NODE_TYPE_HTR,
    HEATER_NODE_TYPE_HTR_MOD,
    PRESET_FROST,
    PRESET_SCHEDULE,
    PRESET_SELF_LEARN,
)
from custom_components.smartbox.model import (
    create_smartbox_device,
    get_devices,
    get_hvac_mode,
    get_preset_mode,
    get_preset_modes,
    get_target_temperature,
    is_heater_node,
    is_heating,
    is_supported_node,
    set_hvac_mode_args,
    set_preset_mode_status_update,
    set_temperature_args,
    SmartboxDevice,
    SmartboxNode,
)

from mocks import mock_device, mock_node
from test_utils import assert_log_message

_LOGGER = logging.getLogger(__name__)


async def test_create_smartbox_device(hass):
    dev_1_id = "test_device_id_1"
    reconnect_attempts = 3
    backoff_factor = 0.1
    mock_dev = mock_device(dev_1_id, [])
    mock_session = MagicMock()
    with patch(
        "custom_components.smartbox.model.SmartboxDevice",
        autospec=True,
        return_value=mock_dev,
    ) as device_ctor_mock:
        device = await create_smartbox_device(
            hass, dev_1_id, "Device 1", mock_session, reconnect_attempts, backoff_factor
        )
        device_ctor_mock.assert_called_with(
            dev_1_id, "Device 1", mock_session, reconnect_attempts, backoff_factor
        )
        mock_dev.initialise_nodes.assert_awaited_with(hass)
        assert device == mock_dev


async def test_get_devices(hass, mock_smartbox):
    dev_1_id = "test_device_id_1"
    dev_1_name = "Device 1"
    dev_2_id = "test_device_id_2"  # missing
    dev_2_name = "Device 2"  # missing
    reconnect_attempts = mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][
        CONF_SOCKET_RECONNECT_ATTEMPTS
    ]
    backoff_factor = mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][
        CONF_SOCKET_BACKOFF_FACTOR
    ]
    test_devices = [
        SmartboxDevice(
            dev["dev_id"],
            dev["name"],
            mock_smartbox.session,
            reconnect_attempts,
            backoff_factor,
        )
        for dev in mock_smartbox.session.get_devices()
    ]
    with patch(
        "custom_components.smartbox.model.create_smartbox_device",
        autospec=True,
        side_effect=test_devices,
    ) as create_smartbox_device_mock:
        # check we called the smartbox API correctly
        devices = await get_devices(
            hass,
            mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][CONF_API_NAME],
            mock_smartbox.config[DOMAIN][CONF_BASIC_AUTH_CREDS],
            mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][CONF_USERNAME],
            mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][CONF_PASSWORD],
            mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][CONF_SESSION_RETRY_ATTEMPTS],
            mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][CONF_SESSION_BACKOFF_FACTOR],
            mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][
                CONF_SOCKET_RECONNECT_ATTEMPTS
            ],
            mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][CONF_SOCKET_BACKOFF_FACTOR],
        )

        # check we created the devices
        create_smartbox_device_mock.assert_any_await(
            hass,
            dev_1_id,
            dev_1_name,
            mock_smartbox.session,
            reconnect_attempts,
            backoff_factor,
        )
        create_smartbox_device_mock.assert_any_await(
            hass,
            dev_2_id,
            dev_2_name,
            mock_smartbox.session,
            reconnect_attempts,
            backoff_factor,
        )
        assert devices == test_devices


async def test_smartbox_device_init(hass, mock_smartbox):
    mock_device = mock_smartbox.get_devices()[0]
    dev_id = mock_device["dev_id"]

    node_sentinel_1 = MagicMock()
    node_sentinel_2 = MagicMock()
    with patch(
        "custom_components.smartbox.model.SmartboxNode",
        side_effect=[node_sentinel_1, node_sentinel_2],
        autospec=True,
    ) as smartbox_node_ctor_mock:
        device = SmartboxDevice(dev_id, "Device 1", mock_smartbox.session, 7, 0.2)
        assert device.dev_id == dev_id
        await device.initialise_nodes(hass)
        mock_smartbox.session.get_nodes.assert_called_with(dev_id)

        nodes = list(device.get_nodes())
        mock_nodes = mock_smartbox.session.get_nodes(dev_id)
        assert len(nodes) == len(mock_nodes)

        mock_smartbox.session.get_status.assert_any_call(dev_id, mock_nodes[0])
        mock_smartbox.session.get_status.assert_any_call(dev_id, mock_nodes[1])

        smartbox_node_ctor_mock.assert_any_call(
            device,
            mock_nodes[0],
            mock_smartbox.session,
            mock_smartbox.session.get_status(dev_id, mock_nodes[0]),
            mock_smartbox.session.get_setup(dev_id, mock_nodes[0]),
        )
        smartbox_node_ctor_mock.assert_any_call(
            device,
            mock_nodes[1],
            mock_smartbox.session,
            mock_smartbox.session.get_status(dev_id, mock_nodes[1]),
            mock_smartbox.session.get_setup(dev_id, mock_nodes[1]),
        )

        assert mock_smartbox.get_socket(dev_id) is not None


async def test_smartbox_device_dev_data_updates(hass):
    """Independently test device data updates usually done by UpdateManager"""
    dev_id = "test_device_id_1"
    mock_session = MagicMock()
    mock_node_1 = MagicMock()
    mock_node_2 = MagicMock()
    # Simulate initialise_nodes with mock data, make sure nobody calls the real one
    with patch(
        "custom_components.smartbox.model.SmartboxDevice.initialise_nodes",
        new_callable=NonCallableMock,
    ):
        device = SmartboxDevice(dev_id, "Device 1", mock_session, 5, 0.3)
        device._nodes = {
            (HEATER_NODE_TYPE_HTR, 1): mock_node_1,
            (HEATER_NODE_TYPE_ACM, 2): mock_node_2,
        }

        mock_dev_data = {"away": True}
        device._away_status_update(mock_dev_data)
        assert device.away

        mock_dev_data = {"away": False}
        device._away_status_update(mock_dev_data)
        assert not device.away

        device._power_limit_update(1045)
        assert device.power_limit == 1045


async def test_smartbox_device_node_status_update(hass, caplog):
    """Independently test node status updates usually called by UpdateManager"""
    dev_id = "test_device_id_1"
    mock_session = MagicMock()
    mock_node_1 = MagicMock()
    mock_node_2 = MagicMock()
    # Simulate initialise_nodes with mock data, make sure nobody calls the real one
    with patch(
        "custom_components.smartbox.model.SmartboxDevice.initialise_nodes",
        new_callable=NonCallableMock,
    ):
        device = SmartboxDevice(dev_id, "Device 1", mock_session, 2, 0.1)
        device._nodes = {
            (HEATER_NODE_TYPE_HTR, 1): mock_node_1,
            (HEATER_NODE_TYPE_ACM, 2): mock_node_2,
        }

        mock_status = {"foo": "bar"}
        device._node_status_update(HEATER_NODE_TYPE_HTR, 1, mock_status)
        mock_node_1.update_status.assert_called_with(mock_status)
        mock_node_2.update_status.assert_not_called()

        mock_node_1.reset_mock()
        mock_node_2.reset_mock()
        device._node_status_update(HEATER_NODE_TYPE_ACM, 2, mock_status)
        mock_node_2.update_status.assert_called_with(mock_status)
        mock_node_1.update_status.assert_not_called()

        # test unknown node
        mock_node_1.reset_mock()
        mock_node_2.reset_mock()
        device._node_status_update(HEATER_NODE_TYPE_HTR, 3, mock_status)
        mock_node_1.update_status.assert_not_called()
        mock_node_2.update_status.assert_not_called()
        assert_log_message(
            caplog,
            "custom_components.smartbox.model",
            logging.ERROR,
            "Received status update for unknown node htr 3",
        )


async def test_smartbox_device_node_setup_update(hass, caplog):
    """Independently test node setup updates usually called by UpdateManager"""
    dev_id = "test_device_id_1"
    mock_session = MagicMock()
    mock_node_1 = MagicMock()
    mock_node_2 = MagicMock()
    # Simulate initialise_nodes with mock data, make sure nobody calls the real one
    with patch(
        "custom_components.smartbox.model.SmartboxDevice.initialise_nodes",
        new_callable=NonCallableMock,
    ):
        device = SmartboxDevice(dev_id, "Device 1", mock_session, 2, 0.1)
        device._nodes = {
            (HEATER_NODE_TYPE_HTR, 1): mock_node_1,
            (HEATER_NODE_TYPE_ACM, 2): mock_node_2,
        }

        mock_setup = {"foo": "bar"}
        device._node_setup_update(HEATER_NODE_TYPE_HTR, 1, mock_setup)
        mock_node_1.update_setup.assert_called_with(mock_setup)
        mock_node_2.update_setup.assert_not_called()

        mock_node_1.reset_mock()
        mock_node_2.reset_mock()
        device._node_setup_update(HEATER_NODE_TYPE_ACM, 2, mock_setup)
        mock_node_2.update_setup.assert_called_with(mock_setup)
        mock_node_1.update_setup.assert_not_called()

        # test unknown node
        mock_node_1.reset_mock()
        mock_node_2.reset_mock()
        device._node_setup_update(HEATER_NODE_TYPE_HTR, 3, mock_setup)
        mock_node_1.update_setup.assert_not_called()
        mock_node_2.update_setup.assert_not_called()
        assert_log_message(
            caplog,
            "custom_components.smartbox.model",
            logging.ERROR,
            "Received setup update for unknown node htr 3",
        )


async def test_smartbox_node(hass):
    dev_id = "test_device_id_1"
    mock_device = MagicMock()
    mock_device.dev_id = dev_id
    mock_device.away = False
    node_addr = 3
    node_type = HEATER_NODE_TYPE_HTR
    node_name = "Bathroom Heater"
    node_info = {"addr": node_addr, "name": node_name, "type": node_type}
    mock_session = MagicMock()
    initial_status = {"mtemp": "21.4", "stemp": "22.5"}
    initial_setup = {"true_radiant_enabled": False, "window_mode_enabled": False}

    node = SmartboxNode(
        mock_device, node_info, mock_session, initial_status, initial_setup
    )
    assert node.node_id == f"{dev_id}-{node_addr}"
    assert node.name == node_name
    assert node.node_type == node_type
    assert node.addr == node_addr

    assert node.status == initial_status
    new_status = {"mtemp": "21.6", "stemp": "22.5"}
    node.update_status(new_status)
    assert node.status == new_status

    node.set_status(stemp=23.5)
    mock_session.set_status.assert_called_with(dev_id, node_info, {"stemp": 23.5})

    assert not node.away
    mock_device.away = True
    assert node.away

    status_update = await node.async_update(hass)
    assert status_update == node.status

    # setup fields
    assert not node.window_mode
    node.update_setup({"window_mode_enabled": True})
    assert node.window_mode
    node.update_setup({})
    with pytest.raises(KeyError):
        node.window_mode

    node.update_setup(initial_setup)
    assert not node.true_radiant
    node.update_setup({"true_radiant_enabled": True})
    assert node.true_radiant
    node.update_setup({})
    with pytest.raises(KeyError):
        node.true_radiant


def test_is_heater_node():
    dev_id = "test_device_id_1"
    addr = 1
    assert is_heater_node(mock_node(dev_id, addr, HEATER_NODE_TYPE_HTR))
    assert is_heater_node(mock_node(dev_id, addr, HEATER_NODE_TYPE_HTR_MOD))
    assert is_heater_node(mock_node(dev_id, addr, HEATER_NODE_TYPE_ACM))
    assert not is_heater_node(mock_node(dev_id, addr, "sldkfjsd"))


def test_is_supported_node():
    dev_id = "test_device_id_1"
    addr = 1
    assert is_supported_node(mock_node(dev_id, addr, HEATER_NODE_TYPE_HTR))
    assert is_supported_node(mock_node(dev_id, addr, HEATER_NODE_TYPE_HTR_MOD))
    assert is_supported_node(mock_node(dev_id, addr, HEATER_NODE_TYPE_ACM))
    assert not is_supported_node(mock_node(dev_id, addr, "oijijr"))


def test_get_target_temperature():
    assert get_target_temperature(HEATER_NODE_TYPE_HTR, {"stemp": "22.5"}) == 22.5
    assert get_target_temperature(HEATER_NODE_TYPE_ACM, {"stemp": "12.6"}) == 12.6
    with pytest.raises(KeyError):
        get_target_temperature(HEATER_NODE_TYPE_HTR, {"xxx": "22.5"})

    assert (
        get_target_temperature(
            HEATER_NODE_TYPE_HTR_MOD,
            {
                "selected_temp": "comfort",
                "comfort_temp": "17.2",
            },
        )
        == 17.2
    )
    assert (
        get_target_temperature(
            HEATER_NODE_TYPE_HTR_MOD,
            {
                "selected_temp": "eco",
                "comfort_temp": "17.2",
                "eco_offset": "4",
            },
        )
        == 13.2
    )
    assert (
        get_target_temperature(
            HEATER_NODE_TYPE_HTR_MOD,
            {
                "selected_temp": "ice",
                "ice_temp": "7",
            },
        )
        == 7
    )

    with pytest.raises(KeyError) as exc_info:
        get_target_temperature(
            HEATER_NODE_TYPE_HTR_MOD,
            {
                "selected_temp": "comfort",
            },
        )
    assert "comfort_temp" in exc_info.exconly()
    with pytest.raises(KeyError) as exc_info:
        get_target_temperature(
            HEATER_NODE_TYPE_HTR_MOD,
            {
                "selected_temp": "eco",
                "comfort_temp": "17.2",
            },
        )
    assert "eco_offset" in exc_info.exconly()
    with pytest.raises(KeyError) as exc_info:
        get_target_temperature(
            HEATER_NODE_TYPE_HTR_MOD,
            {
                "selected_temp": "ice",
            },
        )
    assert "ice_temp" in exc_info.exconly()
    with pytest.raises(KeyError) as exc_info:
        get_target_temperature(
            HEATER_NODE_TYPE_HTR_MOD,
            {
                "selected_temp": "blah",
            },
        )
    assert "Unexpected 'selected_temp' value blah" in exc_info.exconly()


def test_set_temperature_args():
    assert set_temperature_args(HEATER_NODE_TYPE_HTR, {"units": "C"}, 21.7) == {
        "stemp": "21.7",
        "units": "C",
    }
    assert set_temperature_args(HEATER_NODE_TYPE_ACM, {"units": "F"}, 78) == {
        "stemp": "78",
        "units": "F",
    }
    with pytest.raises(KeyError) as exc_info:
        set_temperature_args(HEATER_NODE_TYPE_HTR, {}, 24.7)
    assert "units" in exc_info.exconly()

    assert set_temperature_args(
        HEATER_NODE_TYPE_HTR_MOD,
        {
            "mode": "auto",
            "selected_temp": "comfort",
            "comfort_temp": "18.2",
            "eco_offset": "4",
            "units": "C",
        },
        17.2,
    ) == {
        "on": True,
        "mode": "auto",
        "selected_temp": "comfort",
        "comfort_temp": "17.2",
        "eco_offset": "4",
        "units": "C",
    }
    assert set_temperature_args(
        HEATER_NODE_TYPE_HTR_MOD,
        {
            "mode": "auto",
            "selected_temp": "eco",
            "comfort_temp": "17.2",
            "eco_offset": "4",
            "units": "C",
        },
        14.2,
    ) == {
        "on": True,
        "mode": "auto",
        "selected_temp": "eco",
        "comfort_temp": "18.2",
        "eco_offset": "4",
        "units": "C",
    }
    with pytest.raises(ValueError) as exc_info:
        set_temperature_args(
            HEATER_NODE_TYPE_HTR_MOD,
            {
                "mode": "auto",
                "selected_temp": "ice",
                "ice_temp": "7",
                "units": "C",
            },
            7,
        )
    assert "ice mode" in exc_info.exconly()

    with pytest.raises(KeyError) as exc_info:
        set_temperature_args(
            HEATER_NODE_TYPE_HTR_MOD,
            {
                "mode": "auto",
                "selected_temp": "eco",
                "comfort_temp": "17.2",
                "units": "C",
            },
            17.2,
        )
    assert "eco_offset" in exc_info.exconly()
    with pytest.raises(KeyError) as exc_info:
        set_temperature_args(
            HEATER_NODE_TYPE_HTR_MOD,
            {
                "mode": "auto",
                "selected_temp": "blah",
                "comfort_temp": "17.2",
                "units": "C",
            },
            17.2,
        )
    assert "Unexpected 'selected_temp' value blah" in exc_info.exconly()


def test_get_hvac_mode():
    assert get_hvac_mode(HEATER_NODE_TYPE_HTR, {"mode": "off"}) == HVAC_MODE_OFF
    assert get_hvac_mode(HEATER_NODE_TYPE_ACM, {"mode": "auto"}) == HVAC_MODE_AUTO
    assert (
        get_hvac_mode(HEATER_NODE_TYPE_HTR, {"mode": "modified_auto"}) == HVAC_MODE_AUTO
    )
    assert get_hvac_mode(HEATER_NODE_TYPE_ACM, {"mode": "manual"}) == HVAC_MODE_HEAT
    with pytest.raises(ValueError):
        get_hvac_mode(HEATER_NODE_TYPE_HTR, {"mode": "blah"})
    assert (
        get_hvac_mode(HEATER_NODE_TYPE_HTR_MOD, {"on": True, "mode": "auto"})
        == HVAC_MODE_AUTO
    )
    assert (
        get_hvac_mode(HEATER_NODE_TYPE_HTR_MOD, {"on": True, "mode": "self_learn"})
        == HVAC_MODE_AUTO
    )
    assert (
        get_hvac_mode(HEATER_NODE_TYPE_HTR_MOD, {"on": True, "mode": "presence"})
        == HVAC_MODE_AUTO
    )
    assert (
        get_hvac_mode(HEATER_NODE_TYPE_HTR_MOD, {"on": True, "mode": "manual"})
        == HVAC_MODE_HEAT
    )
    assert (
        get_hvac_mode(HEATER_NODE_TYPE_HTR_MOD, {"on": False, "mode": "auto"})
        == HVAC_MODE_OFF
    )
    assert (
        get_hvac_mode(HEATER_NODE_TYPE_HTR_MOD, {"on": False, "mode": "self_learn"})
        == HVAC_MODE_OFF
    )
    assert (
        get_hvac_mode(HEATER_NODE_TYPE_HTR_MOD, {"on": False, "mode": "presence"})
        == HVAC_MODE_OFF
    )
    assert (
        get_hvac_mode(HEATER_NODE_TYPE_HTR_MOD, {"on": False, "mode": "manual"})
        == HVAC_MODE_OFF
    )
    with pytest.raises(ValueError):
        get_hvac_mode(HEATER_NODE_TYPE_HTR_MOD, {"on": True, "mode": "blah"})
    with pytest.raises(KeyError) as exc_info:
        get_hvac_mode(HEATER_NODE_TYPE_HTR_MOD, {"mode": "manual"})
    assert "on" in exc_info.exconly()


def test_set_hvac_mode_args():
    assert set_hvac_mode_args(HEATER_NODE_TYPE_HTR, {}, HVAC_MODE_OFF) == {
        "mode": "off"
    }
    assert set_hvac_mode_args(HEATER_NODE_TYPE_ACM, {}, HVAC_MODE_AUTO) == {
        "mode": "auto"
    }
    assert set_hvac_mode_args(HEATER_NODE_TYPE_HTR, {}, HVAC_MODE_HEAT) == {
        "mode": "manual"
    }
    with pytest.raises(ValueError):
        set_hvac_mode_args(HEATER_NODE_TYPE_HTR, {}, "blah")
    assert set_hvac_mode_args(
        HEATER_NODE_TYPE_HTR_MOD,
        {},
        HVAC_MODE_OFF,
    ) == {
        "on": False,
    }
    assert set_hvac_mode_args(
        HEATER_NODE_TYPE_HTR_MOD,
        {},
        HVAC_MODE_AUTO,
    ) == {
        "on": True,
        "mode": "auto",
    }
    assert set_hvac_mode_args(
        HEATER_NODE_TYPE_HTR_MOD,
        {
            "selected_temp": "comfort",
        },
        HVAC_MODE_HEAT,
    ) == {
        "on": True,
        "mode": "manual",
        "selected_temp": "comfort",
    }
    with pytest.raises(ValueError):
        set_hvac_mode_args(
            HEATER_NODE_TYPE_HTR_MOD,
            {},
            "blah",
        )
    with pytest.raises(KeyError) as exc_info:
        set_hvac_mode_args(
            HEATER_NODE_TYPE_HTR_MOD,
            {},
            HVAC_MODE_HEAT,
        )
    assert "selected_temp" in exc_info.exconly()


def test_get_preset_mode():
    assert get_preset_mode(HEATER_NODE_TYPE_HTR, {}, away=True) == PRESET_AWAY
    assert get_preset_mode(HEATER_NODE_TYPE_ACM, {}, away=True) == PRESET_AWAY
    assert get_preset_mode(HEATER_NODE_TYPE_HTR_MOD, {}, away=True) == PRESET_AWAY
    assert get_preset_mode(HEATER_NODE_TYPE_HTR, {}, away=False) == PRESET_HOME
    assert get_preset_mode(HEATER_NODE_TYPE_ACM, {}, away=False) == PRESET_HOME

    assert (
        get_preset_mode(
            HEATER_NODE_TYPE_HTR_MOD,
            {"mode": "manual", "selected_temp": "comfort"},
            away=False,
        )
        == PRESET_COMFORT
    )
    assert (
        get_preset_mode(
            HEATER_NODE_TYPE_HTR_MOD,
            {"mode": "manual", "selected_temp": "eco"},
            away=False,
        )
        == PRESET_ECO
    )
    assert (
        get_preset_mode(
            HEATER_NODE_TYPE_HTR_MOD,
            {"mode": "manual", "selected_temp": "ice"},
            away=False,
        )
        == PRESET_FROST
    )
    assert (
        get_preset_mode(
            HEATER_NODE_TYPE_HTR_MOD,
            {"mode": "auto", "selected_temp": "comfort"},
            away=False,
        )
        == PRESET_SCHEDULE
    )
    assert (
        get_preset_mode(
            HEATER_NODE_TYPE_HTR_MOD,
            {"mode": "presence", "selected_temp": "comfort"},
            away=False,
        )
        == PRESET_ACTIVITY
    )
    assert (
        get_preset_mode(
            HEATER_NODE_TYPE_HTR_MOD,
            {"mode": "self_learn", "selected_temp": "comfort"},
            away=False,
        )
        == PRESET_SELF_LEARN
    )
    with pytest.raises(ValueError) as exc_info:
        get_preset_mode(
            HEATER_NODE_TYPE_HTR_MOD,
            {"mode": "blah", "selected_temp": "comfort"},
            away=False,
        )
    assert "Unknown smartbox node mode" in exc_info.exconly()
    with pytest.raises(ValueError) as exc_info:
        get_preset_mode(
            HEATER_NODE_TYPE_HTR_MOD,
            {"mode": "manual", "selected_temp": "blah"},
            away=False,
        )
    assert "Unexpected 'selected_temp' value" in exc_info.exconly()


def test_get_preset_modes():
    assert get_preset_modes(HEATER_NODE_TYPE_HTR) == [PRESET_AWAY, PRESET_HOME]
    assert get_preset_modes(HEATER_NODE_TYPE_ACM) == [PRESET_AWAY, PRESET_HOME]
    assert get_preset_modes(HEATER_NODE_TYPE_HTR_MOD) == [
        PRESET_ACTIVITY,
        PRESET_AWAY,
        PRESET_COMFORT,
        PRESET_ECO,
        PRESET_FROST,
        PRESET_SCHEDULE,
        PRESET_SELF_LEARN,
    ]


def test_set_preset_mode_status_update():
    assert set_preset_mode_status_update(
        HEATER_NODE_TYPE_HTR_MOD, {}, PRESET_SCHEDULE
    ) == {"on": True, "mode": "auto"}
    assert set_preset_mode_status_update(
        HEATER_NODE_TYPE_HTR_MOD, {}, PRESET_SELF_LEARN
    ) == {"on": True, "mode": "self_learn"}
    assert set_preset_mode_status_update(
        HEATER_NODE_TYPE_HTR_MOD, {}, PRESET_ACTIVITY
    ) == {"on": True, "mode": "presence"}
    assert set_preset_mode_status_update(
        HEATER_NODE_TYPE_HTR_MOD, {}, PRESET_COMFORT
    ) == {"on": True, "mode": "manual", "selected_temp": "comfort"}
    assert set_preset_mode_status_update(HEATER_NODE_TYPE_HTR_MOD, {}, PRESET_ECO) == {
        "on": True,
        "mode": "manual",
        "selected_temp": "eco",
    }
    assert set_preset_mode_status_update(
        HEATER_NODE_TYPE_HTR_MOD, {}, PRESET_FROST
    ) == {"on": True, "mode": "manual", "selected_temp": "ice"}

    with pytest.raises(ValueError):
        set_preset_mode_status_update(HEATER_NODE_TYPE_HTR, {}, PRESET_SCHEDULE)
    with pytest.raises(ValueError):
        set_preset_mode_status_update(HEATER_NODE_TYPE_ACM, {}, PRESET_ACTIVITY)

    with pytest.raises(ValueError):
        set_preset_mode_status_update(HEATER_NODE_TYPE_HTR_MOD, {}, "fake_preset")
    with pytest.raises(AssertionError):
        set_preset_mode_status_update(HEATER_NODE_TYPE_HTR_MOD, {}, PRESET_HOME)
    with pytest.raises(AssertionError):
        set_preset_mode_status_update(HEATER_NODE_TYPE_HTR_MOD, {}, PRESET_AWAY)


def test_status_to_hvac_action():
    assert is_heating(HEATER_NODE_TYPE_HTR, {"active": True})
    assert not is_heating(HEATER_NODE_TYPE_HTR, {"active": False})
    assert is_heating(HEATER_NODE_TYPE_ACM, {"charging": True})
    assert not is_heating(HEATER_NODE_TYPE_ACM, {"charging": False})
    assert is_heating(HEATER_NODE_TYPE_HTR_MOD, {"active": True})
    assert not is_heating(HEATER_NODE_TYPE_HTR_MOD, {"active": False})
    with pytest.raises(KeyError):
        is_heating(HEATER_NODE_TYPE_HTR, {})
    with pytest.raises(KeyError):
        is_heating(HEATER_NODE_TYPE_ACM, {"active": True})
