"""Tests for the alert window UI."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from src.ui.alert_window import AlertWindow, AlertState


class TestAlertWindow:
    """Tests for AlertWindow class."""
    
    def test_initial_state(self):
        """Test initial state is IDLE."""
        window = AlertWindow()
        
        assert window.state == AlertState.IDLE
        assert window.total_count == 0
    
    def test_notify_chat(self):
        """Test chat notification changes state."""
        window = AlertWindow()
        
        # Use internal method for testing (notify_chat queues for async processing)
        window._process_chat()
        
        assert window.state == AlertState.CHAT
        assert window.total_count == 1
    
    def test_notify_mention(self):
        """Test mention notification changes state."""
        window = AlertWindow()
        
        # Use internal method for testing
        window._process_mention()
        
        assert window.state == AlertState.MENTION
        assert window.total_count == 1
    
    def test_mention_overrides_chat(self):
        """Test that mention state takes priority over chat."""
        window = AlertWindow()
        
        window._process_chat()
        assert window.state == AlertState.CHAT
        
        window._process_mention()
        assert window.state == AlertState.MENTION
    
    def test_chat_does_not_override_mention(self):
        """Test that chat does not override mention state."""
        window = AlertWindow()
        
        window._process_mention()
        assert window.state == AlertState.MENTION
        
        window._process_chat()
        assert window.state == AlertState.MENTION  # Still mention
        assert window.total_count == 2
    
    def test_reset(self):
        """Test reset returns to idle state."""
        window = AlertWindow()
        
        window._process_chat()
        window._process_mention()
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
        assert window._mention_count == 0
    
    def test_mixed_notifications(self):
        """Test mixed notification types."""
        window = AlertWindow()
        
        window._process_chat()
        window._process_mention()
        window._process_chat()
        
        assert window.total_count == 3
        assert window._chat_count == 2
        assert window._mention_count == 1
        assert window.state == AlertState.MENTION
    
    def test_notify_queues_notification(self):
        """Test that notify_chat and notify_mention queue notifications."""
        window = AlertWindow()
        
        # These should queue notifications, not process immediately
        window.notify_chat()
        window.notify_mention()
        
        # Queue should have 2 items
        assert window._notification_queue.qsize() == 2


class TestAlertState:
    """Tests for AlertState enum."""
    
    def test_states_exist(self):
        """Test all expected states exist."""
        assert AlertState.IDLE
        assert AlertState.CHAT
        assert AlertState.MENTION
    
    def test_states_unique(self):
        """Test states are unique."""
        states = [AlertState.IDLE, AlertState.CHAT, AlertState.MENTION]
        assert len(states) == len(set(states))
