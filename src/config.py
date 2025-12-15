"""Configuration settings for Teams Notifier."""

from dataclasses import dataclass
from typing import Literal


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
    
    # Webhook settings - leave empty to disable
    webhook_url: str | None = ""


# Global config instance
config = Config()
