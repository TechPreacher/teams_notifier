"""Tests for webhook sender."""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from src.webhook.sender import WebhookSender


class TestWebhookSender:
    """Tests for WebhookSender class."""
    
    def test_init_with_url(self):
        """Test initialization with a webhook URL."""
        sender = WebhookSender("https://example.com/webhook")
        assert sender.webhook_url == "https://example.com/webhook"
        assert sender.enabled is True
    
    def test_init_without_url(self):
        """Test initialization without a webhook URL."""
        sender = WebhookSender(None)
        assert sender.webhook_url is None
        assert sender.enabled is False
    
    def test_init_with_empty_url(self):
        """Test initialization with empty webhook URL."""
        sender = WebhookSender("")
        assert sender.webhook_url == ""
        assert sender.enabled is False
    
    def test_send_notification_disabled(self):
        """Test that send_notification returns False when disabled."""
        sender = WebhookSender(None)
        result = asyncio.get_event_loop().run_until_complete(
            sender.send_notification("message")
        )
        assert result is False
    
    def test_send_notification_success(self):
        """Test successful webhook notification."""
        sender = WebhookSender("https://example.com/webhook")
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        async def run_test():
            with patch.object(sender, '_get_session', return_value=mock_session):
                return await sender.send_notification("message")
        
        result = asyncio.get_event_loop().run_until_complete(run_test())
        assert result is True
    
    def test_send_notification_types(self):
        """Test that all notification types can be sent."""
        sender = WebhookSender("https://example.com/webhook")
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        # Test all three notification types
        for notification_type in ["message", "urgent", "clear"]:
            async def run_test(ntype=notification_type):
                with patch.object(sender, '_get_session', return_value=mock_session):
                    return await sender.send_notification(ntype)
            
            result = asyncio.get_event_loop().run_until_complete(run_test())
            assert result is True, f"Failed for type: {notification_type}"
