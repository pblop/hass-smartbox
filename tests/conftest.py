import pytest
from unittest.mock import patch

from const import MOCK_CONFIG_3
from mocks import MockSmartbox

pytest_plugins = "pytest_homeassistant_custom_component"


# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


@pytest.fixture
def mock_smartbox():
    mock_smartbox = MockSmartbox(MOCK_CONFIG_3)

    with patch(
        "custom_components.smartbox.model.Session",
        autospec=True,
        return_value=mock_smartbox.session,
    ):
        with patch(
            "custom_components.smartbox.model.SocketSession",
            autospec=True,
            side_effect=mock_smartbox.get_mock_socket,
        ):
            yield mock_smartbox
