"""Configuration settings for Teams Notifier."""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _find_and_load_dotenv() -> None:
    """Find and load .env file from multiple possible locations."""
    # Possible locations for .env file:
    # 1. Next to the .app bundle (for macOS app)
    # 2. In ~/.config/teams-notifier/
    # 3. In user's home directory
    # 4. Current working directory (development)

    possible_paths = []

    # If running as a bundled app, check next to the .app
    if getattr(sys, "frozen", False):
        # Running as compiled app
        app_dir = Path(
            sys.executable
        ).parent.parent.parent.parent  # .app/Contents/MacOS/exe -> .app parent
        possible_paths.append(app_dir / ".env")
        possible_paths.append(app_dir / "teams-notifier.env")

    # Check ~/.config/teams-notifier/
    config_dir = Path.home() / ".config" / "teams-notifier"
    possible_paths.append(config_dir / ".env")

    # Check home directory
    possible_paths.append(Path.home() / ".teams-notifier.env")

    # Check current working directory (development)
    possible_paths.append(Path.cwd() / ".env")

    # Try each path
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(env_path)
            return

    # Fall back to default load_dotenv behavior
    load_dotenv()


# Load environment variables from .env file
_find_and_load_dotenv()


def _get_webhook_url() -> str | None:
    """Get webhook URL from environment variable."""
    url = os.getenv("WEBHOOK_URL")
    return url if url else None


def _get_webhook_bearer() -> str | None:
    """Get webhook bearer token from environment variable.

    If WEBHOOK_BEARER is set, it will be used as the Authorization header:
    Authorization: Bearer <token>
    """
    token = os.getenv("WEBHOOK_BEARER")
    return token if token else None


def _get_log_level() -> str:
    """Get log level from environment variable.

    Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
    Default: INFO
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if level not in valid_levels:
        return "INFO"
    return level


def _get_urgent_sound_patterns() -> list[str]:
    """Get urgent sound patterns from environment variable.

    Patterns are comma-separated substrings to match in Teams sound names.
    Example: URGENT_SOUND_PATTERNS=urgent,prioritize,escalate,alarm
    """
    patterns = os.getenv("URGENT_SOUND_PATTERNS")
    if patterns:
        return [p.strip().lower() for p in patterns.split(",") if p.strip()]
    # Default patterns that match Teams urgent/priority notification sounds
    return ["urgent", "prioritize", "escalate", "alarm"]


def _get_chat_sound_patterns() -> list[str]:
    """Get chat sound patterns from environment variable.

    Patterns are comma-separated substrings to match in Teams sound names.
    Example: CHAT_SOUND_PATTERNS=basic,ping,notify
    """
    patterns = os.getenv("CHAT_SOUND_PATTERNS")
    if patterns:
        return [p.strip().lower() for p in patterns.split(",") if p.strip()]
    # Default patterns that match Teams basic notification sounds
    return ["basic", "ping", "notify"]


def _get_webhook_payload(env_var: str) -> dict[str, Any] | None:
    """Get webhook payload from environment variable.

    The environment variable should contain a valid JSON object.
    Example: WEBHOOK_PAYLOAD_MESSAGE={"userId": "123", "actionFields": {"color": "yellow"}}

    Args:
        env_var: The name of the environment variable to read.

    Returns:
        The parsed JSON payload as a dict, or None if not set or invalid.
    """
    payload_str = os.getenv(env_var)
    if not payload_str:
        return None
    try:
        payload = json.loads(payload_str)
        if isinstance(payload, dict):
            return payload
        return None
    except json.JSONDecodeError:
        return None


def _get_webhook_payload_message() -> dict[str, Any] | None:
    """Get webhook payload for regular message notifications."""
    return _get_webhook_payload("WEBHOOK_PAYLOAD_MESSAGE")


def _get_webhook_payload_urgent() -> dict[str, Any] | None:
    """Get webhook payload for urgent notifications."""
    return _get_webhook_payload("WEBHOOK_PAYLOAD_URGENT")


def _get_webhook_payload_clear() -> dict[str, Any] | None:
    """Get webhook payload for clear/reset notifications."""
    return _get_webhook_payload("WEBHOOK_PAYLOAD_CLEAR")


@dataclass
class Config:
    """Application configuration."""

    # Logging
    log_level: str = field(default_factory=_get_log_level)

    # Window settings
    window_width: int = 150
    window_height: int = 260
    window_title: str = "Teams Alert"

    # Alert settings
    auto_reset_seconds: int | None = None  # None = manual reset only

    # Sound settings (relative to project root)
    chat_sound: str = "resources/audio/GLaDOS-teams-message.wav"
    urgent_sound: str = "resources/audio/GLaDOS-teams-urgent.wav"
    muted_sound: str = "resources/audio/GLaDOS-teams-muted.wav"
    unmuted_sound: str = "resources/audio/GLaDOS-teams-unmuted.wav"
    sound_enabled: bool = True

    # Teams app bundle identifier
    teams_bundle_id: str = "com.microsoft.teams2"  # New Teams
    teams_bundle_id_classic: str = "com.microsoft.teams"  # Classic Teams

    # Colors (CSS format)
    color_idle: str = "#22c55e"  # Green
    color_chat: str = "#eab308"  # Yellow
    color_urgent: str = "#ef4444"  # Red
    color_muted: str = "#335d94"  # Dark blue (when muted)

    # Mute state
    muted: bool = False

    # Animation speeds (in seconds)
    pulse_speed: float = 1.0
    flash_speed: float = 0.3

    # Webhook settings (loaded from WEBHOOK_URL environment variable)
    webhook_url: str | None = field(default_factory=_get_webhook_url)

    # Webhook bearer token for Authorization header (loaded from WEBHOOK_BEARER)
    webhook_bearer: str | None = field(default_factory=_get_webhook_bearer)

    # Webhook payloads (loaded from environment variables)
    # These are JSON objects sent to the webhook for each notification type
    # If not set, a default payload with type/timestamp/source is used
    webhook_payload_message: dict[str, Any] | None = field(
        default_factory=_get_webhook_payload_message
    )
    webhook_payload_urgent: dict[str, Any] | None = field(
        default_factory=_get_webhook_payload_urgent
    )
    webhook_payload_clear: dict[str, Any] | None = field(
        default_factory=_get_webhook_payload_clear
    )

    # Teams notification sound patterns (loaded from environment variables)
    # These are substrings to match in the sound name Teams plays
    urgent_sound_patterns: list[str] = field(default_factory=_get_urgent_sound_patterns)
    chat_sound_patterns: list[str] = field(default_factory=_get_chat_sound_patterns)


# Global config instance
config = Config()
