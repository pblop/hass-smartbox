import logging
from unittest.mock import patch

from homeassistant.setup import async_setup_component

from smartbox import __version__ as SMARTBOX_VERSION

from custom_components.smartbox import __version__
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
    SMARTBOX_DEVICES,
)
from const import TEST_CONFIG_1, TEST_CONFIG_2, TEST_CONFIG_3
from mocks import mock_device, mock_node

_LOGGER = logging.getLogger(__name__)


async def test_setup_basic(hass, caplog):
    dev_1_id = "test_device_id_1"
    mock_node_1 = mock_node(dev_1_id, 1, HEATER_NODE_TYPE_HTR)
    mock_node_2 = mock_node(dev_1_id, 2, HEATER_NODE_TYPE_HTR_MOD)
    mock_dev_1 = mock_device(dev_1_id, [mock_node_1, mock_node_2])

    with patch(
        "custom_components.smartbox.get_devices",
        autospec=True,
        return_value=[mock_dev_1],
    ) as get_devices_mock:
        assert await async_setup_component(hass, "smartbox", TEST_CONFIG_1)
        await hass.async_block_till_done()
        get_devices_mock.assert_any_await(
            hass,
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_API_NAME],
            TEST_CONFIG_1[DOMAIN][CONF_BASIC_AUTH_CREDS],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_USERNAME],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_PASSWORD],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_SESSION_RETRY_ATTEMPTS],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_SESSION_BACKOFF_FACTOR],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_SOCKET_RECONNECT_ATTEMPTS],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_SOCKET_BACKOFF_FACTOR],
        )
    assert mock_dev_1 in hass.data[DOMAIN][SMARTBOX_DEVICES]

    assert (
        "custom_components.smartbox",
        logging.INFO,
        f"Setting up Smartbox integration v{__version__}"
        f" (using smartbox v{SMARTBOX_VERSION})",
    ) in caplog.record_tuples


async def test_setup_multiple_accounts_and_devices(hass):
    dev_1_id = "test_device_id_1"
    mock_dev_1_node_1 = mock_node(dev_1_id, 1, HEATER_NODE_TYPE_HTR_MOD)
    mock_dev_1 = mock_device(dev_1_id, [mock_dev_1_node_1])

    dev_2_1_id = "test_device_id_2_1"
    mock_dev_2_1_node_1 = mock_node(dev_2_1_id, 1, HEATER_NODE_TYPE_HTR)
    mock_dev_2_1 = mock_device(dev_2_1_id, [mock_dev_2_1_node_1])

    dev_2_2_id = "test_device_id_2_2"
    mock_dev_2_2_node_1 = mock_node(dev_2_2_id, 1, HEATER_NODE_TYPE_ACM)
    mock_dev_2_2 = mock_device(dev_2_2_id, [mock_dev_2_2_node_1])

    devs = [[mock_dev_1], [mock_dev_2_1, mock_dev_2_2]]

    with patch(
        "custom_components.smartbox.get_devices",
        autospec=True,
        side_effect=devs,
    ) as get_devices_mock:
        assert await async_setup_component(hass, "smartbox", TEST_CONFIG_2)
        # first account
        get_devices_mock.assert_any_await(
            hass,
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][0][CONF_API_NAME],
            TEST_CONFIG_2[DOMAIN][CONF_BASIC_AUTH_CREDS],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][0][CONF_USERNAME],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][0][CONF_PASSWORD],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][0][CONF_SESSION_RETRY_ATTEMPTS],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][0][CONF_SESSION_BACKOFF_FACTOR],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][0][CONF_SOCKET_RECONNECT_ATTEMPTS],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][0][CONF_SOCKET_BACKOFF_FACTOR],
        )
        # second account
        get_devices_mock.assert_any_await(
            hass,
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][1][CONF_API_NAME],
            TEST_CONFIG_2[DOMAIN][CONF_BASIC_AUTH_CREDS],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][1][CONF_USERNAME],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][1][CONF_PASSWORD],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][1][CONF_SESSION_RETRY_ATTEMPTS],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][1][CONF_SESSION_BACKOFF_FACTOR],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][1][CONF_SOCKET_RECONNECT_ATTEMPTS],
            TEST_CONFIG_2[DOMAIN][CONF_ACCOUNTS][1][CONF_SOCKET_BACKOFF_FACTOR],
        )
    assert mock_dev_1 in hass.data[DOMAIN][SMARTBOX_DEVICES]
    assert mock_dev_2_1 in hass.data[DOMAIN][SMARTBOX_DEVICES]
    assert mock_dev_2_2 in hass.data[DOMAIN][SMARTBOX_DEVICES]


async def test_setup_missing_and_extra_devices(hass, caplog):
    # config specifies devices 1 and 2, but 2 is missing and 3 exists
    dev_1_id = "test_device_id_1"
    mock_node_1 = mock_node(dev_1_id, 1, HEATER_NODE_TYPE_ACM)
    mock_node_2 = mock_node(dev_1_id, 2, HEATER_NODE_TYPE_HTR_MOD)
    mock_dev_1 = mock_device(dev_1_id, [mock_node_1, mock_node_2])

    dev_2_id = "test_device_id_2"  # missing

    dev_3_id = "test_device_id_3"
    mock_node_1 = mock_node(dev_3_id, 1, HEATER_NODE_TYPE_HTR)
    mock_dev_3 = mock_device(dev_3_id, [mock_node_1])

    with patch(
        "custom_components.smartbox.get_devices",
        autospec=True,
        return_value=[mock_dev_1, mock_dev_3],
    ) as get_devices_mock:
        assert await async_setup_component(hass, "smartbox", TEST_CONFIG_3)
        get_devices_mock.assert_any_await(
            hass,
            TEST_CONFIG_3[DOMAIN][CONF_ACCOUNTS][0][CONF_API_NAME],
            TEST_CONFIG_3[DOMAIN][CONF_BASIC_AUTH_CREDS],
            TEST_CONFIG_3[DOMAIN][CONF_ACCOUNTS][0][CONF_USERNAME],
            TEST_CONFIG_3[DOMAIN][CONF_ACCOUNTS][0][CONF_PASSWORD],
            TEST_CONFIG_3[DOMAIN][CONF_ACCOUNTS][0][CONF_SESSION_RETRY_ATTEMPTS],
            TEST_CONFIG_3[DOMAIN][CONF_ACCOUNTS][0][CONF_SESSION_BACKOFF_FACTOR],
            TEST_CONFIG_3[DOMAIN][CONF_ACCOUNTS][0][CONF_SOCKET_RECONNECT_ATTEMPTS],
            TEST_CONFIG_3[DOMAIN][CONF_ACCOUNTS][0][CONF_SOCKET_BACKOFF_FACTOR],
        )
    assert mock_dev_1 in hass.data[DOMAIN][SMARTBOX_DEVICES]
    assert mock_dev_3 not in hass.data[DOMAIN][SMARTBOX_DEVICES]

    assert (
        "custom_components.smartbox",
        logging.ERROR,
        f"Configured device {dev_2_id} was not found",
    ) in caplog.record_tuples
    assert (
        "custom_components.smartbox",
        logging.WARNING,
        f"Found device {dev_3_id} which was not configured - ignoring",
    ) in caplog.record_tuples


async def test_setup_unsupported_nodes(hass, caplog):
    dev_1_id = "test_device_id_1"
    mock_node_1 = mock_node(dev_1_id, 1, HEATER_NODE_TYPE_HTR_MOD)
    mock_node_2 = mock_node(dev_1_id, 2, "test_unsupported_node")
    mock_dev_1 = mock_device(dev_1_id, [mock_node_1, mock_node_2])

    with patch(
        "custom_components.smartbox.get_devices",
        autospec=True,
        return_value=[mock_dev_1],
    ) as get_devices_mock:
        assert await async_setup_component(hass, "smartbox", TEST_CONFIG_1)
        get_devices_mock.assert_any_await(
            hass,
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_API_NAME],
            TEST_CONFIG_1[DOMAIN][CONF_BASIC_AUTH_CREDS],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_USERNAME],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_PASSWORD],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_SESSION_RETRY_ATTEMPTS],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_SESSION_BACKOFF_FACTOR],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_SOCKET_RECONNECT_ATTEMPTS],
            TEST_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_SOCKET_BACKOFF_FACTOR],
        )
    assert (
        "custom_components.smartbox",
        logging.ERROR,
        'Nodes of type "test_unsupported_node" are not yet supported; '
        "no entities will be created. Please file an issue on GitHub.",
    ) in caplog.record_tuples
