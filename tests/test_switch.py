from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.components.switch import SERVICE_TURN_ON, SERVICE_TURN_OFF
from homeassistant.const import ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME
from homeassistant.setup import async_setup_component

from mocks import (
    get_entity_id_from_unique_id,
    get_object_id,
    get_away_status_switch_entity_id,
    get_away_status_switch_entity_name,
    get_device_unique_id,
)


async def test_away_status(hass, mock_smartbox):
    assert await async_setup_component(hass, "smartbox", mock_smartbox.config)
    await hass.async_block_till_done()

    for mock_device in mock_smartbox.session.get_devices():
        entity_id = get_away_status_switch_entity_id(mock_device)
        state = hass.states.get(entity_id)

        # check basic properties
        assert state.object_id.startswith(
            get_object_id(get_away_status_switch_entity_name(mock_device))
        )
        assert state.entity_id.startswith(get_away_status_switch_entity_id(mock_device))
        assert state.name == f"{mock_device['name']} Away Status"
        assert (
            state.attributes[ATTR_FRIENDLY_NAME] == f"{mock_device['name']} Away Status"
        )
        unique_id = get_device_unique_id(mock_device, "away_status")
        assert entity_id == get_entity_id_from_unique_id(hass, SWITCH_DOMAIN, unique_id)

        # Starts not away
        assert state.state == "off"

    # Set device 1 to away
    mock_device_1 = mock_smartbox.session.get_devices()[0]
    mock_smartbox.dev_data_update(mock_device_1, {"away_status": {"away": True}})

    entity_id = get_away_status_switch_entity_id(mock_device_1)
    await hass.helpers.entity_component.async_update_entity(entity_id)
    state = hass.states.get(entity_id)
    assert state.state == "on"

    mock_device_2 = mock_smartbox.session.get_devices()[1]
    entity_id = get_away_status_switch_entity_id(mock_device_2)
    await hass.helpers.entity_component.async_update_entity(entity_id)
    state = hass.states.get(entity_id)
    assert state.state == "off"

    # Turn off via HA
    entity_id = get_away_status_switch_entity_id(mock_device_1)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.helpers.entity_component.async_update_entity(entity_id)
    state = hass.states.get(entity_id)
    assert state.state == "off"

    # Turn device 2 to away via HA
    entity_id = get_away_status_switch_entity_id(mock_device_2)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.helpers.entity_component.async_update_entity(entity_id)
    state = hass.states.get(entity_id)
    assert state.state == "on"
