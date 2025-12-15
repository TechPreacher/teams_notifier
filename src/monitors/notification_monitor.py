"""macOS Notification Center monitor for Teams notifications."""

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any

# macOS frameworks
import objc
from Foundation import (
    NSDistributedNotificationCenter,
    NSObject,
    NSRunLoop,
    NSDate,
)

from ..config import config

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Type of Teams notification."""
    CHAT = auto()
    MENTION = auto()
    UNKNOWN = auto()


@dataclass
class TeamsNotification:
    """Represents a Teams notification."""
    type: NotificationType
    timestamp: datetime
    raw_data: dict | None = None


class NotificationObserver(NSObject):
    """Objective-C observer for distributed notifications."""
    
    def initWithCallback_(self, callback: Callable[[dict], None]):
        """Initialize with a Python callback."""
        self = objc.super(NotificationObserver, self).init()
        if self is None:
            return None
        self._callback = callback
        return self
    
    def handleNotification_(self, notification):
        """Handle incoming notification."""
        try:
            user_info = notification.userInfo()
            name = notification.name()
            obj = notification.object()
            
            data = {
                "name": str(name) if name else None,
                "object": str(obj) if obj else None,
                "userInfo": dict(user_info) if user_info else None,
            }
            
            if self._callback:
                self._callback(data)
        except Exception as e:
            logger.error(f"Error handling notification: {e}")


class NotificationMonitor:
    """Monitors macOS notifications for Teams activity."""
    
    def __init__(self):
        self._observer: NotificationObserver | None = None
        self._callbacks: list[Callable[[TeamsNotification], None]] = []
        self._running = False
        self._thread: threading.Thread | None = None
        self._center = NSDistributedNotificationCenter.defaultCenter()
    
    def add_callback(self, callback: Callable[[TeamsNotification], None]) -> None:
        """Register a callback for Teams notifications."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[TeamsNotification], None]) -> None:
        """Remove a registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _handle_raw_notification(self, data: dict) -> None:
        """Process raw notification and dispatch to callbacks."""
        notification = self._parse_notification(data)
        
        if notification.type != NotificationType.UNKNOWN:
            logger.info(f"Teams notification detected: {notification.type.name}")
            for callback in self._callbacks:
                try:
                    callback(notification)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def _parse_notification(self, data: dict) -> TeamsNotification:
        """Parse raw notification data into a TeamsNotification.
        
        Attempts to distinguish between:
        - CHAT: Direct messages (1:1 or group chat)
        - MENTION: @mentions in Teams channels
        
        Note: This detection is based on notification content patterns and may not
        be 100% accurate as macOS notification metadata is limited.
        """
        name = data.get("name", "") or ""
        obj = data.get("object", "") or ""
        user_info = data.get("userInfo", {}) or {}
        
        # Check if this is a Teams notification
        is_teams = any([
            config.teams_bundle_id in obj,
            config.teams_bundle_id_classic in obj,
            config.teams_bundle_id in name,
            config.teams_bundle_id_classic in name,
            "teams" in obj.lower(),
            "teams" in name.lower(),
        ])
        
        if not is_teams:
            return TeamsNotification(
                type=NotificationType.UNKNOWN,
                timestamp=datetime.now(),
                raw_data=data,
            )
        
        # Log raw data for debugging (helps tune detection)
        logger.debug(f"Teams notification raw data: {data}")
        
        # Build searchable strings from notification content
        info_str = str(user_info).lower()
        name_str = name.lower()
        combined = f"{info_str} {name_str}"
        
        # Determine notification type based on content patterns
        notification_type = self._classify_notification(combined, user_info)
        
        return TeamsNotification(
            type=notification_type,
            timestamp=datetime.now(),
            raw_data=data,
        )
    
    def _classify_notification(self, content: str, user_info: dict) -> NotificationType:
        """Classify notification type based on content analysis.
        
        Channel mentions typically contain:
        - "@" symbol or "mentioned" keyword
        - Channel/team names
        - "replied to" patterns
        
        Direct chats typically contain:
        - Just sender name and message
        - No channel indicators
        """
        # Strong indicators of a channel mention
        mention_patterns = [
            "@",                    # Direct @ mention
            "mentioned",            # "mentioned you"
            "replied to",           # Reply to your message
            "replied in",           # Reply in thread
            "tagged",               # Tagged in message
            " in #",                # "mentioned you in #channel"
            "channel",              # Channel notifications
            "team:",                # Team name prefix
        ]
        
        # Check for mention indicators
        for pattern in mention_patterns:
            if pattern in content:
                logger.debug(f"Detected MENTION (pattern: '{pattern}')")
                return NotificationType.MENTION
        
        # Check userInfo for specific keys that might indicate type
        if user_info:
            # These keys might exist in notification payload
            info_keys = str(user_info.keys()).lower()
            if any(k in info_keys for k in ["channel", "team", "mention"]):
                logger.debug("Detected MENTION (from userInfo keys)")
                return NotificationType.MENTION
        
        # Default to CHAT for direct messages
        logger.debug("Classified as CHAT (no mention indicators found)")
        return NotificationType.CHAT
    
    def start(self) -> None:
        """Start monitoring notifications."""
        if self._running:
            return
        
        self._running = True
        
        # Create observer
        self._observer = NotificationObserver.alloc().initWithCallback_(
            self._handle_raw_notification
        )
        
        # Register for all distributed notifications (we'll filter for Teams)
        # This catches notifications from the NotificationCenter
        self._center.addObserver_selector_name_object_(
            self._observer,
            objc.selector(self._observer.handleNotification_, signature=b"v@:@"),
            None,  # All notification names
            None,  # All objects
        )
        
        logger.info("Notification monitor started")
    
    def stop(self) -> None:
        """Stop monitoring notifications."""
        if not self._running:
            return
        
        self._running = False
        
        if self._observer:
            self._center.removeObserver_(self._observer)
            self._observer = None
        
        logger.info("Notification monitor stopped")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


# Alternative approach using SQLite database monitoring
# Teams stores notification state in a local database that we can watch
class TeamsDBMonitor:
    """
    Alternative monitor that watches Teams' local database for changes.
    This is more reliable but depends on Teams' internal implementation.
    
    Note: This is a backup approach if distributed notifications don't work well.
    """
    
    def __init__(self):
        self._db_path = self._find_teams_db()
        self._running = False
        self._last_check = datetime.now()
    
    def _find_teams_db(self) -> str | None:
        """Locate the Teams SQLite database."""
        import os
        from pathlib import Path
        
        # Common paths for Teams data
        possible_paths = [
            Path.home() / "Library/Application Support/Microsoft/Teams",
            Path.home() / "Library/Group Containers/UBF8T346G9.com.microsoft.teams",
            Path.home() / "Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/Teams",
        ]
        
        for base_path in possible_paths:
            if base_path.exists():
                # Look for IndexedDB or sqlite files
                for db_file in base_path.rglob("*.db"):
                    return str(db_file)
                for db_file in base_path.rglob("*.sqlite"):
                    return str(db_file)
        
        return None
    
    @property
    def available(self) -> bool:
        """Check if database monitoring is available."""
        return self._db_path is not None
