"""Tests for the alert window UI."""

from unittest.mock import MagicMock

from src.ui.alert_window import AlertWindow, AlertState
from src.config import config


class TestAlertWindow:
    """Tests for AlertWindow class."""

    def test_initial_state(self):
        """Test initial state is IDLE."""
        window = AlertWindow()

        assert window.state == AlertState.IDLE
        assert window.total_count == 0

    def test_initial_mute_state(self):
        """Test initial mute state matches config."""
        original_muted = config.muted
        try:
            config.muted = False
            window = AlertWindow()
            assert window.muted is False

            config.muted = True
            window2 = AlertWindow()
            assert window2.muted is True
        finally:
            config.muted = original_muted

    def test_notify_chat(self):
        """Test chat notification changes state."""
        window = AlertWindow()

        # Use internal method for testing (notify_chat queues for async processing)
        window._process_chat()

        assert window.state == AlertState.CHAT
        assert window.total_count == 1

    def test_notify_urgent(self):
        """Test urgent notification changes state."""
        window = AlertWindow()

        # Use internal method for testing
        window._process_urgent()

        assert window.state == AlertState.URGENT
        assert window.total_count == 1

    def test_urgent_overrides_chat(self):
        """Test that urgent state takes priority over chat."""
        window = AlertWindow()

        window._process_chat()
        assert window.state == AlertState.CHAT

        window._process_urgent()
        assert window.state == AlertState.URGENT

    def test_chat_does_not_override_urgent(self):
        """Test that chat does not override urgent state."""
        window = AlertWindow()

        window._process_urgent()
        assert window.state == AlertState.URGENT

        window._process_chat()
        assert window.state == AlertState.URGENT  # Still urgent
        assert window.total_count == 2

    def test_reset(self):
        """Test reset returns to idle state."""
        window = AlertWindow()

        window._process_chat()
        window._process_urgent()
        assert window.total_count == 2

        window.reset()

        assert window.state == AlertState.IDLE
        assert window.total_count == 0

    def test_reset_callback(self):
        """Test reset callback is invoked."""
        window = AlertWindow()
        callback = MagicMock()
        window.on_reset(callback)

        window._process_chat()
        window.reset()

        callback.assert_called_once()

    def test_multiple_notifications(self):
        """Test multiple notifications increment count."""
        window = AlertWindow()

        window._process_chat()
        window._process_chat()
        window._process_chat()

        assert window.total_count == 3
        assert window._chat_count == 3
        assert window._urgent_count == 0

    def test_mixed_notifications(self):
        """Test mixed notification types."""
        window = AlertWindow()

        window._process_chat()
        window._process_urgent()
        window._process_chat()

        assert window.total_count == 3
        assert window._chat_count == 2
        assert window._urgent_count == 1
        assert window.state == AlertState.URGENT

    def test_notify_queues_notification(self):
        """Test that notify_chat and notify_urgent queue notifications."""
        window = AlertWindow()

        # These should queue notifications, not process immediately
        window.notify_chat()
        window.notify_urgent()

        # Queue should have 2 items
        assert window._notification_queue.qsize() == 2

    def test_toggle_mute(self):
        """Test toggling mute state."""
        original_muted = config.muted
        try:
            config.muted = False
            window = AlertWindow()

            assert window.muted is False

            window.toggle_mute()
            assert window.muted is True
            assert config.muted is True

            window.toggle_mute()
            assert window.muted is False
            assert config.muted is False
        finally:
            config.muted = original_muted

    def test_mute_callback(self):
        """Test mute callback is invoked with correct state."""
        original_muted = config.muted
        try:
            config.muted = False
            window = AlertWindow()
            callback = MagicMock()
            window.on_mute(callback)

            window.toggle_mute()
            callback.assert_called_once_with(True)

            callback.reset_mock()
            window.toggle_mute()
            callback.assert_called_once_with(False)
        finally:
            config.muted = original_muted

    def test_on_mute_clears_existing_callbacks(self):
        """Test that on_mute clears existing callbacks before adding new one.

        This prevents double audio feedback when the page is refreshed/revisited.
        """
        original_muted = config.muted
        try:
            config.muted = False
            window = AlertWindow()

            callback1 = MagicMock()
            callback2 = MagicMock()

            # Register first callback
            window.on_mute(callback1)
            # Register second callback (should replace first)
            window.on_mute(callback2)

            window.toggle_mute()

            # Only callback2 should be called (callback1 was cleared)
            callback1.assert_not_called()
            callback2.assert_called_once_with(True)
        finally:
            config.muted = original_muted

    def test_on_reset_clears_existing_callbacks(self):
        """Test that on_reset clears existing callbacks before adding new one.

        This prevents duplicate callback execution when the page is refreshed.
        """
        window = AlertWindow()

        callback1 = MagicMock()
        callback2 = MagicMock()

        # Register first callback
        window.on_reset(callback1)
        # Register second callback (should replace first)
        window.on_reset(callback2)

        window._process_chat()
        window.reset()

        # Only callback2 should be called (callback1 was cleared)
        callback1.assert_not_called()
        callback2.assert_called_once()

    def test_mute_preserves_notification_count(self):
        """Test that muting preserves notification count."""
        original_muted = config.muted
        try:
            config.muted = False
            window = AlertWindow()

            window._process_chat()
            window._process_urgent()
            assert window.total_count == 2

            window.toggle_mute()
            assert window.muted is True
            assert window.total_count == 2  # Count preserved

            window._process_chat()  # Should still count while muted
            assert window.total_count == 3
        finally:
            config.muted = original_muted

    def test_reset_does_not_affect_mute(self):
        """Test that reset does not change mute state."""
        original_muted = config.muted
        try:
            config.muted = False
            window = AlertWindow()

            window.toggle_mute()
            assert window.muted is True

            window._process_chat()
            window.reset()

            assert window.muted is True  # Still muted after reset
            assert window.total_count == 0
        finally:
            config.muted = original_muted


class TestAlertState:
    """Tests for AlertState enum."""

    def test_states_exist(self):
        """Test all expected states exist."""
        assert AlertState.IDLE
        assert AlertState.CHAT
        assert AlertState.URGENT

    def test_states_unique(self):
        """Test states are unique."""
        states = [AlertState.IDLE, AlertState.CHAT, AlertState.URGENT]
        assert len(states) == len(set(states))
