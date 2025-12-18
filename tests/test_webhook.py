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

    def test_init_with_custom_payloads(self):
        """Test initialization with custom payloads."""
        custom_message = {"userId": "123", "color": "yellow"}
        custom_urgent = {"userId": "123", "color": "red"}
        custom_clear = {"userId": "123", "color": "green"}

        sender = WebhookSender(
            webhook_url="https://example.com/webhook",
            payload_message=custom_message,
            payload_urgent=custom_urgent,
            payload_clear=custom_clear,
        )

        assert sender._payloads["message"] == custom_message
        assert sender._payloads["urgent"] == custom_urgent
        assert sender._payloads["clear"] == custom_clear

    def test_get_payload_with_custom(self):
        """Test _get_payload returns custom payload when configured."""
        custom_payload = {"userId": "test-123", "actionFields": {"color": "red"}}
        sender = WebhookSender(
            webhook_url="https://example.com/webhook",
            payload_urgent=custom_payload,
        )

        payload = sender._get_payload("urgent")
        assert payload == custom_payload

    def test_get_payload_default(self):
        """Test _get_payload returns default payload when not configured."""
        sender = WebhookSender(webhook_url="https://example.com/webhook")

        payload = sender._get_payload("message")

        assert "type" in payload
        assert payload["type"] == "message"
        assert "timestamp" in payload
        assert "source" in payload
        assert payload["source"] == "teams-notifier"

    def test_get_payload_partial_custom(self):
        """Test _get_payload with only some custom payloads configured."""
        custom_urgent = {"custom": "urgent-payload"}
        sender = WebhookSender(
            webhook_url="https://example.com/webhook",
            payload_urgent=custom_urgent,
        )

        # Custom payload should be returned for urgent
        urgent_payload = sender._get_payload("urgent")
        assert urgent_payload == custom_urgent

        # Default payload should be returned for message
        message_payload = sender._get_payload("message")
        assert message_payload["type"] == "message"
        assert "timestamp" in message_payload

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
            with patch.object(sender, "_get_session", return_value=mock_session):
                return await sender.send_notification("message")

        result = asyncio.get_event_loop().run_until_complete(run_test())
        assert result is True

    def test_send_notification_with_custom_payload(self):
        """Test webhook sends custom payload when configured."""
        custom_payload = {"userId": "abc", "actionFields": {"color": "yellow"}}
        sender = WebhookSender(
            webhook_url="https://example.com/webhook",
            payload_message=custom_payload,
        )

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False

        async def run_test():
            with patch.object(sender, "_get_session", return_value=mock_session):
                return await sender.send_notification("message")

        result = asyncio.get_event_loop().run_until_complete(run_test())
        assert result is True

        # Verify the custom payload was sent
        call_args = mock_session.post.call_args
        assert call_args.kwargs["json"] == custom_payload

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
                with patch.object(sender, "_get_session", return_value=mock_session):
                    return await sender.send_notification(ntype)

            result = asyncio.get_event_loop().run_until_complete(run_test())
            assert result is True, f"Failed for type: {notification_type}"
