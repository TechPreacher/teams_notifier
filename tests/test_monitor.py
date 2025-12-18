"""Tests for the log stream notification monitor."""

from unittest.mock import MagicMock
from datetime import datetime

from src.monitors.log_stream_monitor import (
    LogStreamMonitor,
    NotificationType,
    TeamsNotification,
)


class TestLogStreamMonitor:
    """Tests for LogStreamMonitor class."""

    def test_notification_pattern_matches_teams2(self):
        """Test that the pattern matches Teams notification log lines."""
        monitor = LogStreamMonitor()

        log_line = (
            'Queuing action present for app com.microsoft.teams2 items: ["761F-2077"]'
        )

        assert monitor.NOTIFICATION_PATTERN.search(log_line) is not None

    def test_notification_pattern_matches_classic_teams(self):
        """Test that the pattern matches classic Teams notification log lines."""
        monitor = LogStreamMonitor()

        log_line = (
            'Queuing action present for app com.microsoft.teams items: ["ABC-123"]'
        )

        assert monitor.NOTIFICATION_PATTERN.search(log_line) is not None

    def test_notification_pattern_ignores_other_apps(self):
        """Test that the pattern ignores non-Teams apps."""
        monitor = LogStreamMonitor()

        log_line = 'Queuing action present for app com.apple.mail items: ["XYZ-789"]'

        assert monitor.NOTIFICATION_PATTERN.search(log_line) is None

    def test_sound_pattern_matches(self):
        """Test that the sound pattern matches Teams notification sounds."""
        monitor = LogStreamMonitor()

        log_line = "Playing notification sound { nam: a8_teams_basic_notification_r4_ping } for com.microsoft.teams2"

        match = monitor.SOUND_PATTERN.search(log_line)
        assert match is not None
        assert match.group(1) == "a8_teams_basic_notification_r4_ping"

    def test_classify_by_sound_basic_is_chat(self):
        """Test that basic notification sounds are classified as CHAT."""
        monitor = LogStreamMonitor()

        sound_names = [
            "a8_teams_basic_notification_r4_ping",
            "a4_teams_basic_notification_r4_tap",
            "00_teams_basic_notification_r4_default",
        ]

        for sound_name in sound_names:
            notification_type = monitor._classify_by_sound(sound_name)
            assert notification_type == NotificationType.CHAT, (
                f"Expected CHAT for {sound_name}"
            )

    def test_classify_by_sound_urgent_is_urgent(self):
        """Test that urgent notification sounds are classified as URGENT."""
        monitor = LogStreamMonitor()

        sound_names = [
            "b2_teams_urgent_notification_r4_prioritize",
            "b3_teams_urgent_notification_r4_escalate",
            "b4_teams_urgent_notification_r4_alarm",
        ]

        for sound_name in sound_names:
            notification_type = monitor._classify_by_sound(sound_name)
            assert notification_type == NotificationType.URGENT, (
                f"Expected URGENT for {sound_name}"
            )

    def test_callback_registration(self):
        """Test callback registration and removal."""
        monitor = LogStreamMonitor()
        callback = MagicMock()

        monitor.add_callback(callback)
        assert callback in monitor._callbacks

        monitor.remove_callback(callback)
        assert callback not in monitor._callbacks

    def test_debouncing(self):
        """Test that duplicate notifications are debounced."""
        monitor = LogStreamMonitor()
        monitor._debounce_seconds = 1.0

        # First notification should process
        assert monitor._should_process_notification() is True

        # Immediate second notification should be debounced
        assert monitor._should_process_notification() is False

    def test_dispatch_notification(self):
        """Test that notifications are dispatched to callbacks."""
        monitor = LogStreamMonitor()
        callback = MagicMock()
        monitor.add_callback(callback)

        notification = TeamsNotification(
            type=NotificationType.CHAT,
            timestamp=datetime.now(),
        )

        monitor._dispatch_notification(notification)

        callback.assert_called_once_with(notification)

    def test_dispatch_notification_handles_callback_error(self):
        """Test that callback errors don't stop other callbacks."""
        monitor = LogStreamMonitor()

        failing_callback = MagicMock(side_effect=Exception("Test error"))
        working_callback = MagicMock()

        monitor.add_callback(failing_callback)
        monitor.add_callback(working_callback)

        notification = TeamsNotification(
            type=NotificationType.CHAT,
            timestamp=datetime.now(),
        )

        # Should not raise, and should call both callbacks
        monitor._dispatch_notification(notification)

        failing_callback.assert_called_once()
        working_callback.assert_called_once()

    def test_process_sound_then_notification(self):
        """Test that sound line sets pending type for next notification."""
        monitor = LogStreamMonitor()
        callback = MagicMock()
        monitor.add_callback(callback)

        # Process sound line first (urgent sound = URGENT type)
        sound_line = "Playing notification sound { nam: b2_teams_urgent_notification_r4_prioritize } for com.microsoft.teams2"
        monitor._process_log_line(sound_line)

        assert monitor._pending_notification_type == NotificationType.URGENT

        # Then process notification line
        notification_line = (
            'Queuing action present for app com.microsoft.teams2 items: ["ABC-123"]'
        )
        monitor._process_log_line(notification_line)

        # Should have dispatched an URGENT notification
        callback.assert_called_once()
        notification = callback.call_args[0][0]
        assert notification.type == NotificationType.URGENT


class TestTeamsNotification:
    """Tests for TeamsNotification dataclass."""

    def test_notification_creation(self):
        """Test creating a notification."""
        notification = TeamsNotification(
            type=NotificationType.CHAT,
            timestamp=datetime.now(),
        )

        assert notification.type == NotificationType.CHAT
        assert notification.raw_data is None

    def test_notification_with_data(self):
        """Test creating a notification with raw data."""
        raw = {"log_line": "test data"}
        notification = TeamsNotification(
            type=NotificationType.URGENT,
            timestamp=datetime.now(),
            raw_data=raw,
        )

        assert notification.raw_data == raw


class TestNotificationType:
    """Tests for NotificationType enum."""

    def test_types_exist(self):
        """Test all expected types exist."""
        assert NotificationType.CHAT
        assert NotificationType.URGENT
        assert NotificationType.UNKNOWN

    def test_types_unique(self):
        """Test types are unique."""
        types = [
            NotificationType.CHAT,
            NotificationType.URGENT,
            NotificationType.UNKNOWN,
        ]
        assert len(types) == len(set(types))
