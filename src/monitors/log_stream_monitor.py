"""macOS log stream monitor for Teams notifications.

This monitor uses the macOS `log stream` command to detect Teams notifications.
This is more reliable than NSDistributedNotificationCenter for the new Teams app
(com.microsoft.teams2) which uses the User Notifications framework.
"""

import logging
import re
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any

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


class LogStreamMonitor:
    """Monitors macOS log stream for Teams notification events.
    
    This monitor watches the NotificationCenter process for Teams-related
    notification events using the `log stream` command. This approach works
    with the new Microsoft Teams app (com.microsoft.teams2) which uses the
    User Notifications framework.
    """
    
    # Pattern to match Teams notification events
    # Example: "Queuing action present for app com.microsoft.teams2 items: ["761F-2077"]"
    NOTIFICATION_PATTERN = re.compile(
        r'Queuing action present for app (com\.microsoft\.teams2?)\s+items:',
        re.IGNORECASE
    )
    
    # Pattern to extract notification content (if available)
    CONTENT_PATTERN = re.compile(
        r'addOrUpdate listItem:.*?from app com\.microsoft\.teams',
        re.IGNORECASE
    )
    
    # Patterns that suggest a mention vs regular chat
    MENTION_INDICATORS = [
        r'@',
        r'mentioned',
        r'replied to',
        r'replied in',
        r'tagged',
        r'channel',
        r'team:',
    ]
    
    def __init__(self):
        self._callbacks: list[Callable[[TeamsNotification], None]] = []
        self._running = False
        self._process: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._last_notification_time: datetime | None = None
        self._debounce_seconds = 1.0  # Ignore duplicate notifications within this window
    
    def add_callback(self, callback: Callable[[TeamsNotification], None]) -> None:
        """Register a callback for Teams notifications."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[TeamsNotification], None]) -> None:
        """Remove a registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _dispatch_notification(self, notification: TeamsNotification) -> None:
        """Dispatch notification to all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def _should_process_notification(self) -> bool:
        """Check if we should process this notification (debouncing)."""
        now = datetime.now()
        if self._last_notification_time is None:
            self._last_notification_time = now
            return True
        
        elapsed = (now - self._last_notification_time).total_seconds()
        if elapsed < self._debounce_seconds:
            logger.debug(f"Debouncing notification (elapsed: {elapsed:.2f}s)")
            return False
        
        self._last_notification_time = now
        return True
    
    def _classify_notification(self, log_line: str) -> NotificationType:
        """Classify notification type based on log content.
        
        Note: The log stream doesn't always contain the notification content,
        so we default to CHAT. The notification content patterns are checked
        when available.
        """
        log_lower = log_line.lower()
        
        # Check for mention indicators in the log line
        for pattern in self.MENTION_INDICATORS:
            if re.search(pattern, log_lower):
                logger.debug(f"Detected MENTION (pattern: '{pattern}')")
                return NotificationType.MENTION
        
        # Default to CHAT
        return NotificationType.CHAT
    
    def _process_log_line(self, line: str) -> None:
        """Process a single log line and detect Teams notifications."""
        # Check if this is a Teams notification event
        if self.NOTIFICATION_PATTERN.search(line):
            logger.debug(f"Teams notification detected in log: {line[:200]}")
            
            if not self._should_process_notification():
                return
            
            notification_type = self._classify_notification(line)
            
            notification = TeamsNotification(
                type=notification_type,
                timestamp=datetime.now(),
                raw_data={"log_line": line},
            )
            
            logger.info(f"Teams notification detected: {notification_type.name}")
            self._dispatch_notification(notification)
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop that reads from log stream."""
        logger.info("Starting log stream monitor...")
        
        # Build the log stream command
        # Monitor NotificationCenter process for Teams-related events
        predicate = (
            'process == "NotificationCenter" AND '
            '(eventMessage CONTAINS "com.microsoft.teams2" OR '
            'eventMessage CONTAINS "com.microsoft.teams")'
        )
        
        cmd = [
            "log", "stream",
            "--predicate", predicate,
            "--info",
            "--style", "compact"
        ]
        
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )
            
            logger.info("Log stream process started")
            
            # Read lines from the log stream
            while self._running and self._process.poll() is None:
                line = self._process.stdout.readline()
                if line:
                    self._process_log_line(line.strip())
            
            logger.info("Log stream monitor loop ended")
            
        except Exception as e:
            logger.error(f"Error in log stream monitor: {e}")
        finally:
            if self._process:
                self._process.terminate()
                self._process = None
    
    def start(self) -> None:
        """Start monitoring notifications."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
        logger.info("Log stream notification monitor started")
    
    def stop(self) -> None:
        """Stop monitoring notifications."""
        if not self._running:
            return
        
        self._running = False
        
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
        
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        
        logger.info("Log stream notification monitor stopped")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
