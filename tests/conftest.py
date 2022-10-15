from copy import deepcopy
import pytest
from unittest.mock import patch

from const import (
    MOCK_SMARTBOX_CONFIG,
    MOCK_SMARTBOX_NODE_INFO,
    MOCK_SMARTBOX_NODE_STATUS_F,
    MOCK_SMARTBOX_NODE_STATUS_C,
)

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


@pytest.fixture(params=["C", "F"])
def mock_smartbox(request):
    mock_smartbox = MockSmartbox(
        MOCK_SMARTBOX_CONFIG,
        MOCK_SMARTBOX_NODE_INFO,
        deepcopy(
            MOCK_SMARTBOX_NODE_STATUS_C
            if request.param == "C"
            else MOCK_SMARTBOX_NODE_STATUS_F
        ),
    )

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


@pytest.fixture(params=["C", "F"])
def mock_smartbox_unavailable(request):
    mock_smartbox = MockSmartbox(
        MOCK_SMARTBOX_CONFIG,
        MOCK_SMARTBOX_NODE_INFO,
        deepcopy(
            MOCK_SMARTBOX_NODE_STATUS_C
            if request.param == "C"
            else MOCK_SMARTBOX_NODE_STATUS_F
        ),
        False,
    )

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
