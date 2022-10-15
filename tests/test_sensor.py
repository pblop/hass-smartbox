import logging
from pytest import approx

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_LOCKED,
    STATE_UNAVAILABLE,
)
from homeassistant.setup import async_setup_component

from mocks import (
    convert_temp,
    get_entity,
    get_entity_id,
    get_object_id,
    get_unique_id,
    round_temp,
)

_LOGGER = logging.getLogger(__name__)


def _check_temp_state(hass, mock_node_status, state):
    assert round_temp(hass, float(state.state)) == round_temp(
        hass,
        convert_temp(hass, mock_node_status["units"], float(mock_node_status["mtemp"])),
    )


async def test_basic_temp(hass, mock_smartbox):
    assert await async_setup_component(hass, "smartbox", mock_smartbox.config)
    await hass.async_block_till_done()

    for mock_device in mock_smartbox.session.get_devices():
        for mock_node in mock_smartbox.session.get_nodes(mock_device["dev_id"]):
            unique_id = get_unique_id(mock_device, mock_node, "temperature")
            entity_id = get_entity(hass, SENSOR_DOMAIN, unique_id)

            state = hass.states.get(entity_id)

            # check basic properties
            assert state.object_id.startswith(get_object_id(mock_node))
            assert state.entity_id.startswith(get_entity_id(mock_node, SENSOR_DOMAIN))
            assert state.name == mock_node["name"]
            assert state.attributes[ATTR_FRIENDLY_NAME] == mock_node["name"]

            mock_node_status = mock_smartbox.session.get_status(
                mock_device["dev_id"], mock_node
            )
            assert state.attributes[ATTR_LOCKED] == mock_node_status["locked"]
            _check_temp_state(hass, mock_node_status, state)

            mock_smartbox.generate_socket_status_update(
                mock_device,
                mock_node,
                {"mtemp": str(float(mock_node_status["mtemp"]) + 1)},
            )

            await hass.helpers.entity_component.async_update_entity(entity_id)
            new_state = hass.states.get(entity_id)
            assert new_state.state != state.state
            mock_node_status = mock_smartbox.session.get_status(
                mock_device["dev_id"], mock_node
            )
            _check_temp_state(hass, mock_node_status, new_state)

            # test unavailable
            mock_node_status = mock_smartbox.generate_socket_node_unavailable(
                mock_device, mock_node
            )
            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            assert state.state == STATE_UNAVAILABLE

            mock_node_status = mock_smartbox.generate_new_socket_status(
                mock_device, mock_node
            )
            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            assert state.state != STATE_UNAVAILABLE


async def test_basic_power(hass, mock_smartbox):
    assert await async_setup_component(hass, "smartbox", mock_smartbox.config)
    await hass.async_block_till_done()

    for mock_device in mock_smartbox.session.get_devices():
        for mock_node in mock_smartbox.session.get_nodes(mock_device["dev_id"]):
            unique_id = get_unique_id(mock_device, mock_node, "power")
            entity_id = get_entity(hass, SENSOR_DOMAIN, unique_id)

            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)

            # check basic properties
            assert state.object_id.startswith(get_object_id(mock_node))
            assert state.entity_id.startswith(get_entity_id(mock_node, SENSOR_DOMAIN))
            assert state.name == mock_node["name"]
            assert state.attributes[ATTR_FRIENDLY_NAME] == mock_node["name"]

            # make sure it's active
            mock_smartbox.generate_socket_status_update(
                mock_device,
                mock_node,
                {"active": True},
            )
            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            mock_node_status = mock_smartbox.session.get_status(
                mock_device["dev_id"], mock_node
            )
            assert state.attributes[ATTR_LOCKED] == mock_node_status["locked"]
            assert float(state.state) == approx(float(mock_node_status["power"]))

            # make sure it's inactive
            mock_smartbox.generate_socket_status_update(
                mock_device,
                mock_node,
                {"active": False},
            )
            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            mock_node_status = mock_smartbox.session.get_status(
                mock_device["dev_id"], mock_node
            )
            assert float(state.state) == 0

            # test unavailable
            mock_node_status = mock_smartbox.generate_socket_node_unavailable(
                mock_device, mock_node
            )
            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            assert state.state == STATE_UNAVAILABLE

            mock_node_status = mock_smartbox.generate_new_socket_status(
                mock_device, mock_node
            )
            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            assert state.state != STATE_UNAVAILABLE


async def test_unavailable(hass, mock_smartbox_unavailable):
    assert await async_setup_component(
        hass, "smartbox", mock_smartbox_unavailable.config
    )
    await hass.async_block_till_done()

    for mock_device in mock_smartbox_unavailable.session.get_devices():
        for mock_node in mock_smartbox_unavailable.session.get_nodes(
            mock_device["dev_id"]
        ):
            for sensor_type in "temperature", "power":
                unique_id = get_unique_id(mock_device, mock_node, sensor_type)
                entity_id = get_entity(hass, SENSOR_DOMAIN, unique_id)

                state = hass.states.get(entity_id)
                assert state.state == STATE_UNAVAILABLE
