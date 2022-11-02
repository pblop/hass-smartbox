from custom_components.smartbox.const import (
    DOMAIN,
    CONF_ACCOUNTS,
    CONF_API_NAME,
    CONF_BASIC_AUTH_CREDS,
    CONF_DEVICE_IDS,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_SESSION_RETRY_ATTEMPTS,
    CONF_SESSION_BACKOFF_FACTOR,
    CONF_SOCKET_RECONNECT_ATTEMPTS,
    CONF_SOCKET_BACKOFF_FACTOR,
)

TEST_CONFIG_1 = {
    DOMAIN: {
        CONF_ACCOUNTS: [
            {
                CONF_API_NAME: "test_api_name_1",
                CONF_USERNAME: "test_username_1",
                CONF_PASSWORD: "test_password_1",
                CONF_DEVICE_IDS: ["test_device_id_1"],
                CONF_SESSION_RETRY_ATTEMPTS: 4,
                CONF_SESSION_BACKOFF_FACTOR: 0.1,
                CONF_SOCKET_RECONNECT_ATTEMPTS: 3,
                CONF_SOCKET_BACKOFF_FACTOR: 0.2,
            },
        ],
        CONF_BASIC_AUTH_CREDS: "test_basic_auth_creds",
    }
}

TEST_CONFIG_2 = {
    DOMAIN: {
        CONF_ACCOUNTS: [
            {
                CONF_API_NAME: "test_api_name_1",
                CONF_USERNAME: "test_username_1",
                CONF_PASSWORD: "test_password_1",
                CONF_DEVICE_IDS: ["test_device_id_1"],
                CONF_SESSION_RETRY_ATTEMPTS: 5,
                CONF_SESSION_BACKOFF_FACTOR: 0.2,
                CONF_SOCKET_RECONNECT_ATTEMPTS: 4,
                CONF_SOCKET_BACKOFF_FACTOR: 0.3,
            },
            {
                CONF_API_NAME: "test_api_name_2",
                CONF_USERNAME: "test_username_2",
                CONF_PASSWORD: "test_password_2",
                CONF_DEVICE_IDS: ["test_device_id_2_1", "test_device_id_2_2"],
                CONF_SESSION_RETRY_ATTEMPTS: 6,
                CONF_SESSION_BACKOFF_FACTOR: 0.3,
                CONF_SOCKET_RECONNECT_ATTEMPTS: 5,
                CONF_SOCKET_BACKOFF_FACTOR: 0.4,
            },
        ],
        CONF_BASIC_AUTH_CREDS: "test_basic_auth_creds",
    }
}

TEST_CONFIG_3 = {
    DOMAIN: {
        CONF_ACCOUNTS: [
            {
                CONF_API_NAME: "test_api_name_1",
                CONF_USERNAME: "test_username_1",
                CONF_PASSWORD: "test_password_1",
                CONF_DEVICE_IDS: ["test_device_id_1", "test_device_id_2"],
                CONF_SESSION_RETRY_ATTEMPTS: 7,
                CONF_SESSION_BACKOFF_FACTOR: 0.4,
                CONF_SOCKET_RECONNECT_ATTEMPTS: 6,
                CONF_SOCKET_BACKOFF_FACTOR: 0.5,
            },
        ],
        CONF_BASIC_AUTH_CREDS: "test_basic_auth_creds",
    }
}

MOCK_SMARTBOX_CONFIG = {
    DOMAIN: {
        CONF_ACCOUNTS: [
            {
                CONF_API_NAME: "test_api_name_1",
                CONF_USERNAME: "test_username_1",
                CONF_PASSWORD: "test_password_1",
                CONF_DEVICE_IDS: ["test_device_id_1", "test_device_id_2"],
                CONF_SESSION_RETRY_ATTEMPTS: 7,
                CONF_SESSION_BACKOFF_FACTOR: 0.4,
                CONF_SOCKET_RECONNECT_ATTEMPTS: 6,
                CONF_SOCKET_BACKOFF_FACTOR: 0.5,
            },
        ],
        CONF_BASIC_AUTH_CREDS: "test_basic_auth_creds",
    }
}


MOCK_SMARTBOX_NODE_INFO = {
    "test_device_id_1": [
        {
            "addr": 0,
            "name": "Test device 1 node 0",
            "type": "htr",
        },
        {
            "addr": 1,
            "name": "Test device 1 node 1",
            "type": "acm",
        },
    ],
    "test_device_id_2": [
        {
            "addr": 0,
            "name": "Test device 2 node 0",
            "type": "htr_mod",
        },
        {
            "addr": 1,
            "name": "Test device 2 node 1",
            "type": "htr_mod",
        },
        {
            "addr": 2,
            "name": "Test device 2 node 2",
            "type": "htr_mod",
        },
    ],
}

MOCK_SMARTBOX_NODE_STATUS_C = {
    "test_device_id_1": [
        {
            "mtemp": "25.7",
            "stemp": "20.3",
            "units": "C",
            "sync_status": "ok",
            "locked": False,
            "active": True,
            "power": "510",
            "mode": "auto",
        },
        {
            "mtemp": "19.2",
            "stemp": "21",
            "units": "C",
            "sync_status": "ok",
            "locked": False,
            "active": True,
            "power": "620",
            "mode": "manual",
        },
    ],
    "test_device_id_2": [
        {
            "on": True,
            "mtemp": "25.7",
            "selected_temp": "comfort",
            "comfort_temp": "20.3",
            "eco_offset": "4",
            "ice_temp": "7",
            "units": "C",
            "sync_status": "ok",
            "locked": False,
            "active": True,
            "mode": "auto",
        },
        {
            "on": True,
            "mtemp": "19.2",
            "selected_temp": "eco",
            "comfort_temp": "24.3",
            "eco_offset": "4",
            "ice_temp": "7",
            "units": "C",
            "sync_status": "ok",
            "locked": False,
            "active": True,
            "mode": "manual",
        },
        {
            "on": True,
            "mtemp": "17.2",
            "selected_temp": "ice",
            "comfort_temp": "23.3",
            "eco_offset": "4",
            "ice_temp": "7",
            "units": "C",
            "sync_status": "ok",
            "locked": False,
            "active": True,
            "mode": "manual",
        },
    ],
}

MOCK_SMARTBOX_NODE_STATUS_F = {
    "test_device_id_1": [
        {
            "mtemp": "80.7",
            "stemp": "78.3",
            "units": "F",
        },
        {
            "mtemp": "81.2",
            "stemp": "82",
            "units": "F",
        },
    ],
    "test_device_id_2": [
        {
            "mtemp": "80.7",
            "comfort_temp": "78.3",
            "eco_offset": "11",
            "ice_temp": "45",
            "units": "F",
        },
        {
            "mtemp": "81.2",
            "comfort_temp": "93",
            "eco_offset": "11",
            "ice_temp": "45",
            "units": "F",
        },
        {
            "mtemp": "50.7",
            "comfort_temp": "93",
            "eco_offset": "11",
            "ice_temp": "45",
            "units": "F",
        },
    ],
}
