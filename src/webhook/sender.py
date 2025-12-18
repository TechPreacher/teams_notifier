"""Webhook sender for Teams notifications."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional
import threading

import aiohttp
import requests

logger = logging.getLogger(__name__)


class WebhookSender:
    """Sends notification events to a configured webhook."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        payload_message: Optional[dict[str, Any]] = None,
        payload_urgent: Optional[dict[str, Any]] = None,
        payload_clear: Optional[dict[str, Any]] = None,
    ):
        """Initialize the webhook sender.

        Args:
            webhook_url: The URL to send webhook notifications to.
                        If None or empty, webhooks are disabled.
            payload_message: Custom JSON payload for 'message' notifications.
            payload_urgent: Custom JSON payload for 'urgent' notifications.
            payload_clear: Custom JSON payload for 'clear' notifications.
        """
        self.webhook_url = webhook_url
        self._payloads = {
            "message": payload_message,
            "urgent": payload_urgent,
            "clear": payload_clear,
        }
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def enabled(self) -> bool:
        """Check if webhook notifications are enabled."""
        return bool(self.webhook_url)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _get_payload(self, notification_type: str) -> dict[str, Any]:
        """Get the payload for a notification type.

        Args:
            notification_type: Either "message", "urgent", or "clear"

        Returns:
            The custom payload if configured, otherwise a default payload.
        """
        custom_payload = self._payloads.get(notification_type)
        if custom_payload is not None:
            return custom_payload

        # Default payload if no custom payload is configured
        return {
            "type": notification_type,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "teams-notifier",
        }

    async def send_notification(self, notification_type: str) -> bool:
        """Send a notification to the webhook.

        Args:
            notification_type: Either "message", "urgent", or "clear"

        Returns:
            True if the webhook was sent successfully, False otherwise.
        """
        if not self.enabled:
            logger.debug("Webhook not configured, skipping")
            return False

        payload = self._get_payload(notification_type)

        try:
            session = await self._get_session()
            async with session.post(
                self.webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status < 300:
                    logger.info(f"Webhook sent successfully: {notification_type}")
                    return True
                else:
                    logger.warning(
                        f"Webhook returned status {response.status}: {await response.text()}"
                    )
                    return False
        except asyncio.TimeoutError:
            logger.warning("Webhook request timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    def _send_sync_request(self, notification_type: str) -> bool:
        """Send webhook using synchronous requests library.

        This is used when called from a background thread where asyncio
        event loops may not be available or may conflict with the main loop.
        """
        payload = self._get_payload(notification_type)

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code < 300:
                logger.info(f"Webhook sent successfully: {notification_type}")
                return True
            else:
                logger.warning(
                    f"Webhook returned status {response.status_code}: {response.text}"
                )
                return False
        except requests.Timeout:
            logger.warning("Webhook request timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    def send_notification_sync(self, notification_type: str) -> None:
        """Send a notification to the webhook (fire-and-forget from sync context).

        Args:
            notification_type: Either "message", "urgent", or "clear"
        """
        if not self.enabled:
            return

        # Check if we're in the main thread with a running event loop
        if threading.current_thread() is threading.main_thread():
            try:
                asyncio.get_running_loop()
                # We're in the main thread with an async context, schedule the task
                asyncio.create_task(self.send_notification(notification_type))
                logger.debug(f"Scheduled webhook task for: {notification_type}")
                return
            except RuntimeError:
                # No running loop in main thread
                pass

        # We're in a background thread or no event loop - use sync requests
        # Run in a separate thread to avoid blocking
        thread = threading.Thread(
            target=self._send_sync_request, args=(notification_type,), daemon=True
        )
        thread.start()

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
