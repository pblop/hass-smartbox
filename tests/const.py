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
)

MOCK_CONFIG_1 = {
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
            },
        ],
        CONF_BASIC_AUTH_CREDS: "test_basic_auth_creds",
    }
}

MOCK_CONFIG_2 = {
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
            },
            {
                CONF_API_NAME: "test_api_name_2",
                CONF_USERNAME: "test_username_2",
                CONF_PASSWORD: "test_password_2",
                CONF_DEVICE_IDS: ["test_device_id_2_1", "test_device_id_2_2"],
                CONF_SESSION_RETRY_ATTEMPTS: 6,
                CONF_SESSION_BACKOFF_FACTOR: 0.3,
                CONF_SOCKET_RECONNECT_ATTEMPTS: 5,
            },
        ],
        CONF_BASIC_AUTH_CREDS: "test_basic_auth_creds",
    }
}

MOCK_CONFIG_3 = {
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
            },
        ],
        CONF_BASIC_AUTH_CREDS: "test_basic_auth_creds",
    }
}
