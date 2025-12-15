"""Configuration settings for Teams Notifier."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

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
    if getattr(sys, 'frozen', False):
        # Running as compiled app
        app_dir = Path(sys.executable).parent.parent.parent.parent  # .app/Contents/MacOS/exe -> .app parent
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


@dataclass
class Config:
    """Application configuration."""
    
    # Window settings
    window_width: int = 150
    window_height: int = 200
    window_title: str = "Teams Alert"
    
    # Alert settings
    auto_reset_seconds: int | None = None  # None = manual reset only
    
    # Sound settings (relative to project root)
    chat_sound: str = "resources/audio/GLaDOS-teams-message.wav"
    mention_sound: str = "resources/audio/GLaDOS-teams-mention.wav"
    sound_enabled: bool = True
    
    # Teams app bundle identifier
    teams_bundle_id: str = "com.microsoft.teams2"  # New Teams
    teams_bundle_id_classic: str = "com.microsoft.teams"  # Classic Teams
    
    # Colors (CSS format)
    color_idle: str = "#22c55e"  # Green
    color_chat: str = "#eab308"  # Yellow
    color_mention: str = "#ef4444"  # Red
    
    # Animation speeds (in seconds)
    pulse_speed: float = 1.0
    flash_speed: float = 0.3
    
    # Webhook settings (loaded from WEBHOOK_URL environment variable)
    webhook_url: str | None = field(default_factory=_get_webhook_url)


# Global config instance
config = Config()
