"""Tests for the notification monitor."""

import pytest
from unittest.mock import MagicMock, patch

from src.monitors.notification_monitor import (
    NotificationMonitor,
    NotificationType,
    TeamsNotification,
)


class TestNotificationMonitor:
    """Tests for NotificationMonitor class."""
    
    def test_parse_teams_chat_notification(self):
        """Test parsing a Teams chat notification."""
        monitor = NotificationMonitor()
        
        data = {
            "name": "com.apple.notificationcenterui.notification",
            "object": "com.microsoft.teams2",
            "userInfo": {"title": "New message"},
        }
        
        notification = monitor._parse_notification(data)
        
        assert notification.type == NotificationType.CHAT
        assert notification.raw_data == data
    
    def test_parse_teams_mention_notification(self):
        """Test parsing a Teams mention notification."""
        monitor = NotificationMonitor()
        
        data = {
            "name": "com.apple.notificationcenterui.notification",
            "object": "com.microsoft.teams2",
            "userInfo": {"title": "@mentioned you"},
        }
        
        notification = monitor._parse_notification(data)
        
        assert notification.type == NotificationType.MENTION
    
    def test_parse_non_teams_notification(self):
        """Test that non-Teams notifications are ignored."""
        monitor = NotificationMonitor()
        
        data = {
            "name": "com.apple.notificationcenterui.notification",
            "object": "com.apple.mail",
            "userInfo": {"title": "New email"},
        }
        
        notification = monitor._parse_notification(data)
        
        assert notification.type == NotificationType.UNKNOWN
    
    def test_callback_registration(self):
        """Test callback registration and removal."""
        monitor = NotificationMonitor()
        callback = MagicMock()
        
        monitor.add_callback(callback)
        assert callback in monitor._callbacks
        
        monitor.remove_callback(callback)
        assert callback not in monitor._callbacks
    
    def test_callback_invocation(self):
        """Test that callbacks are invoked on notification."""
        monitor = NotificationMonitor()
        callback = MagicMock()
        monitor.add_callback(callback)
        
        # Simulate a Teams notification
        data = {
            "name": "test",
            "object": "com.microsoft.teams2",
            "userInfo": {},
        }
        
        monitor._handle_raw_notification(data)
        
        callback.assert_called_once()
        notification = callback.call_args[0][0]
        assert isinstance(notification, TeamsNotification)


class TestTeamsNotification:
    """Tests for TeamsNotification dataclass."""
    
    def test_notification_creation(self):
        """Test creating a notification."""
        from datetime import datetime
        
        notification = TeamsNotification(
            type=NotificationType.CHAT,
            timestamp=datetime.now(),
        )
        
        assert notification.type == NotificationType.CHAT
        assert notification.raw_data is None
    
    def test_notification_with_data(self):
        """Test creating a notification with raw data."""
        from datetime import datetime
        
        raw = {"test": "data"}
        notification = TeamsNotification(
            type=NotificationType.MENTION,
            timestamp=datetime.now(),
            raw_data=raw,
        )
        
        assert notification.raw_data == raw
