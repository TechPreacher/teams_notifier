"""Sound player for Teams notifications using macOS system sounds."""

import logging
import subprocess
import threading
from pathlib import Path

from ..config import config

logger = logging.getLogger(__name__)

# Get project root directory (for resolving relative paths)
PROJECT_ROOT = Path(__file__).parent.parent.parent


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

    def play_urgent_sound(self) -> None:
        """Play sound for urgent notification."""
        self._play_sound(config.urgent_sound)

    def play_muted_sound(self) -> None:
        """Play sound when muting."""
        self._play_sound_always(config.muted_sound)

    def play_unmuted_sound(self) -> None:
        """Play sound when unmuting."""
        self._play_sound_always(config.unmuted_sound)

    def _resolve_sound_path(self, sound_path: str) -> Path:
        """Resolve sound path, handling both absolute and relative paths."""
        path = Path(sound_path)
        if path.is_absolute():
            return path
        # Resolve relative to project root
        return PROJECT_ROOT / path

    def _play_sound(self, sound_path: str) -> None:
        """Play a sound file using macOS afplay command."""
        if not self._enabled:
            return
        self._play_sound_always(sound_path)

    def _play_sound_always(self, sound_path: str) -> None:
        """Play a sound file regardless of enabled state (for mute/unmute feedback)."""
        # Resolve the path
        resolved_path = self._resolve_sound_path(sound_path)

        # Verify sound file exists
        if not resolved_path.exists():
            logger.warning(f"Sound file not found: {resolved_path}")
            # Fall back to system beep
            self._system_beep()
            return

        # Play sound in background thread to not block
        def _play():
            with self._lock:
                try:
                    subprocess.run(
                        ["afplay", str(resolved_path)],
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

        print("Testing urgent sound...")
        self.play_urgent_sound()
