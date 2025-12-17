"""Tests for the log stream notification monitor."""

import pytest
from unittest.mock import MagicMock, patch
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
        
        log_line = 'Queuing action present for app com.microsoft.teams2 items: ["761F-2077"]'
        
        assert monitor.NOTIFICATION_PATTERN.search(log_line) is not None
    
    def test_notification_pattern_matches_classic_teams(self):
        """Test that the pattern matches classic Teams notification log lines."""
        monitor = LogStreamMonitor()
        
        log_line = 'Queuing action present for app com.microsoft.teams items: ["ABC-123"]'
        
        assert monitor.NOTIFICATION_PATTERN.search(log_line) is not None
    
    def test_notification_pattern_ignores_other_apps(self):
        """Test that the pattern ignores non-Teams apps."""
        monitor = LogStreamMonitor()
        
        log_line = 'Queuing action present for app com.apple.mail items: ["XYZ-789"]'
        
        assert monitor.NOTIFICATION_PATTERN.search(log_line) is None
    
    def test_classify_notification_default_chat(self):
        """Test that notifications default to CHAT type."""
        monitor = LogStreamMonitor()
        
        log_line = 'Some notification log line without mention indicators'
        
        notification_type = monitor._classify_notification(log_line)
        
        assert notification_type == NotificationType.CHAT
    
    def test_classify_notification_mention_at_symbol(self):
        """Test that @ symbol triggers MENTION classification."""
        monitor = LogStreamMonitor()
        
        log_line = 'Notification with @username mention'
        
        notification_type = monitor._classify_notification(log_line)
        
        assert notification_type == NotificationType.MENTION
    
    def test_classify_notification_mention_keyword(self):
        """Test that 'mentioned' keyword triggers MENTION classification."""
        monitor = LogStreamMonitor()
        
        log_line = 'Someone mentioned you in a channel'
        
        notification_type = monitor._classify_notification(log_line)
        
        assert notification_type == NotificationType.MENTION
    
    def test_classify_notification_replied_to(self):
        """Test that 'replied to' triggers MENTION classification."""
        monitor = LogStreamMonitor()
        
        log_line = 'John replied to your message'
        
        notification_type = monitor._classify_notification(log_line)
        
        assert notification_type == NotificationType.MENTION
    
    def test_classify_notification_channel(self):
        """Test that 'channel' keyword triggers MENTION classification."""
        monitor = LogStreamMonitor()
        
        log_line = 'New message in channel General'
        
        notification_type = monitor._classify_notification(log_line)
        
        assert notification_type == NotificationType.MENTION
    
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
            type=NotificationType.MENTION,
            timestamp=datetime.now(),
            raw_data=raw,
        )
        
        assert notification.raw_data == raw


class TestNotificationType:
    """Tests for NotificationType enum."""
    
    def test_types_exist(self):
        """Test all expected types exist."""
        assert NotificationType.CHAT
        assert NotificationType.MENTION
        assert NotificationType.UNKNOWN
    
    def test_types_unique(self):
        """Test types are unique."""
        types = [NotificationType.CHAT, NotificationType.MENTION, NotificationType.UNKNOWN]
        assert len(types) == len(set(types))
