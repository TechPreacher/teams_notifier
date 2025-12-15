"""Sound player for Teams notifications using macOS system sounds."""

import logging
import subprocess
import threading
from pathlib import Path

from ..config import config

logger = logging.getLogger(__name__)


class SoundPlayer:
    """Plays system sounds for notifications."""
    
    def __init__(self):
        self._enabled = config.sound_enabled
        self._lock = threading.Lock()
    
    @property
    def enabled(self) -> bool:
        """Whether sound is enabled."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable sound."""
        self._enabled = value
    
    def play_chat_sound(self) -> None:
        """Play sound for new chat message."""
        self._play_sound(config.chat_sound)
    
    def play_mention_sound(self) -> None:
        """Play sound for mention notification."""
        self._play_sound(config.mention_sound)
    
    def _play_sound(self, sound_path: str) -> None:
        """Play a sound file using macOS afplay command."""
        if not self._enabled:
            return
        
        # Verify sound file exists
        if not Path(sound_path).exists():
            logger.warning(f"Sound file not found: {sound_path}")
            # Fall back to system beep
            self._system_beep()
            return
        
        # Play sound in background thread to not block
        def _play():
            with self._lock:
                try:
                    subprocess.run(
                        ["afplay", sound_path],
                        check=True,
                        capture_output=True,
                    )
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to play sound: {e}")
                except FileNotFoundError:
                    logger.error("afplay command not found")
                    self._system_beep()
        
        thread = threading.Thread(target=_play, daemon=True)
        thread.start()
    
    def _system_beep(self) -> None:
        """Fall back to system beep."""
        try:
            # Use macOS system beep via AppKit
            from AppKit import NSBeep
            NSBeep()
        except ImportError:
            # Last resort: terminal beep
            print("\a", end="", flush=True)
    
    def list_available_sounds(self) -> list[str]:
        """List available system sounds."""
        sounds_dir = Path("/System/Library/Sounds")
        if sounds_dir.exists():
            return sorted([str(f) for f in sounds_dir.glob("*.aiff")])
        return []
    
    def test_sounds(self) -> None:
        """Test both notification sounds."""
        import time
        
        print("Testing chat sound...")
        self.play_chat_sound()
        time.sleep(1.5)
        
        print("Testing mention sound...")
        self.play_mention_sound()
