"""Webhook sender for Teams notifications."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class WebhookSender:
    """Sends notification events to a configured webhook."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize the webhook sender.
        
        Args:
            webhook_url: The URL to send webhook notifications to.
                        If None or empty, webhooks are disabled.
        """
        self.webhook_url = webhook_url
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
    
    async def send_notification(self, notification_type: str) -> bool:
        """Send a notification to the webhook.
        
        Args:
            notification_type: Either "message" or "mention"
            
        Returns:
            True if the webhook was sent successfully, False otherwise.
        """
        if not self.enabled:
            logger.debug("Webhook not configured, skipping")
            return False
        
        payload = {
            "type": notification_type,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "teams-notifier"
        }
        
        try:
            session = await self._get_session()
            async with session.post(
                self.webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
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
    
    def send_notification_sync(self, notification_type: str) -> None:
        """Send a notification to the webhook (fire-and-forget from sync context).
        
        Args:
            notification_type: Either "message" or "mention"
        """
        if not self.enabled:
            return
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule the coroutine to run
                asyncio.create_task(self.send_notification(notification_type))
            else:
                # Run synchronously if no loop is running
                loop.run_until_complete(self.send_notification(notification_type))
        except RuntimeError:
            # No event loop, create one
            asyncio.run(self.send_notification(notification_type))
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
