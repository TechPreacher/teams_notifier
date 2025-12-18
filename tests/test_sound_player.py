"""Tests for the sound player."""

from unittest.mock import patch

from src.audio.sound_player import SoundPlayer
from src.config import config


class TestSoundPlayer:
    """Tests for SoundPlayer class."""

    def test_initial_enabled_state(self):
        """Test initial enabled state matches config."""
        original_enabled = config.sound_enabled
        try:
            config.sound_enabled = True
            player = SoundPlayer()
            assert player.enabled is True

            config.sound_enabled = False
            player2 = SoundPlayer()
            assert player2.enabled is False
        finally:
            config.sound_enabled = original_enabled

    def test_enabled_setter(self):
        """Test enabled property can be set."""
        original_enabled = config.sound_enabled
        try:
            config.sound_enabled = True
            player = SoundPlayer()

            player.enabled = False
            assert player.enabled is False

            player.enabled = True
            assert player.enabled is True
        finally:
            config.sound_enabled = original_enabled

    def test_play_sound_respects_enabled(self):
        """Test that _play_sound does not play when disabled."""
        original_enabled = config.sound_enabled
        original_muted = config.muted
        try:
            config.sound_enabled = False
            config.muted = False
            player = SoundPlayer()

            with patch.object(player, "_play_sound_always") as mock_play:
                player._play_sound("test.wav")
                mock_play.assert_not_called()
        finally:
            config.sound_enabled = original_enabled
            config.muted = original_muted

    def test_play_sound_respects_muted(self):
        """Test that _play_sound does not play when muted.

        This is the key test for the bug fix - notification sounds should
        NOT play when the app is muted.
        """
        original_enabled = config.sound_enabled
        original_muted = config.muted
        try:
            config.sound_enabled = True
            config.muted = True  # App is muted
            player = SoundPlayer()

            with patch.object(player, "_play_sound_always") as mock_play:
                player._play_sound("test.wav")
                mock_play.assert_not_called()
        finally:
            config.sound_enabled = original_enabled
            config.muted = original_muted

    def test_play_sound_plays_when_enabled_and_not_muted(self):
        """Test that _play_sound plays when enabled and not muted."""
        original_enabled = config.sound_enabled
        original_muted = config.muted
        try:
            config.sound_enabled = True
            config.muted = False
            player = SoundPlayer()

            with patch.object(player, "_play_sound_always") as mock_play:
                player._play_sound("test.wav")
                mock_play.assert_called_once_with("test.wav")
        finally:
            config.sound_enabled = original_enabled
            config.muted = original_muted

    def test_play_chat_sound_uses_config_path(self):
        """Test that play_chat_sound uses the configured sound path."""
        original_enabled = config.sound_enabled
        original_muted = config.muted
        try:
            config.sound_enabled = True
            config.muted = False
            player = SoundPlayer()

            with patch.object(player, "_play_sound") as mock_play:
                player.play_chat_sound()
                mock_play.assert_called_once_with(config.chat_sound)
        finally:
            config.sound_enabled = original_enabled
            config.muted = original_muted

    def test_play_urgent_sound_uses_config_path(self):
        """Test that play_urgent_sound uses the configured sound path."""
        original_enabled = config.sound_enabled
        original_muted = config.muted
        try:
            config.sound_enabled = True
            config.muted = False
            player = SoundPlayer()

            with patch.object(player, "_play_sound") as mock_play:
                player.play_urgent_sound()
                mock_play.assert_called_once_with(config.urgent_sound)
        finally:
            config.sound_enabled = original_enabled
            config.muted = original_muted

    def test_play_muted_sound_always_plays(self):
        """Test that play_muted_sound uses _play_sound_always (ignores mute)."""
        original_enabled = config.sound_enabled
        original_muted = config.muted
        try:
            config.sound_enabled = True
            config.muted = True  # Even when muted
            player = SoundPlayer()

            with patch.object(player, "_play_sound_always") as mock_play:
                player.play_muted_sound()
                mock_play.assert_called_once_with(config.muted_sound)
        finally:
            config.sound_enabled = original_enabled
            config.muted = original_muted

    def test_play_unmuted_sound_always_plays(self):
        """Test that play_unmuted_sound uses _play_sound_always (ignores mute)."""
        original_enabled = config.sound_enabled
        original_muted = config.muted
        try:
            config.sound_enabled = True
            config.muted = False
            player = SoundPlayer()

            with patch.object(player, "_play_sound_always") as mock_play:
                player.play_unmuted_sound()
                mock_play.assert_called_once_with(config.unmuted_sound)
        finally:
            config.sound_enabled = original_enabled
            config.muted = original_muted

    def test_mute_toggle_updates_sound_behavior(self):
        """Test that toggling mute in config affects sound playback.

        This simulates the real-world scenario where user toggles mute
        and subsequent notification sounds should respect the mute state.
        """
        original_enabled = config.sound_enabled
        original_muted = config.muted
        try:
            config.sound_enabled = True
            config.muted = False
            player = SoundPlayer()

            with patch.object(player, "_play_sound_always") as mock_play:
                # Sound should play when not muted
                player._play_sound("test.wav")
                assert mock_play.call_count == 1

                # User mutes the app
                config.muted = True

                # Sound should NOT play when muted
                player._play_sound("test.wav")
                assert mock_play.call_count == 1  # Still 1, no new call

                # User unmutes the app
                config.muted = False

                # Sound should play again
                player._play_sound("test.wav")
                assert mock_play.call_count == 2
        finally:
            config.sound_enabled = original_enabled
            config.muted = original_muted

    def test_resolve_sound_path_absolute(self):
        """Test resolving an absolute sound path."""
        player = SoundPlayer()

        path = player._resolve_sound_path("/absolute/path/to/sound.wav")
        assert str(path) == "/absolute/path/to/sound.wav"

    def test_resolve_sound_path_relative(self):
        """Test resolving a relative sound path."""
        player = SoundPlayer()

        path = player._resolve_sound_path("resources/audio/test.wav")
        assert path.is_absolute()
        assert str(path).endswith("resources/audio/test.wav")


class TestSoundPlayerIntegration:
    """Integration tests for sound player with mute state."""

    def test_notification_sound_blocked_when_muted(self):
        """Test that chat/urgent sounds don't play when muted.

        This is the key integration test for the bug fix.
        """
        original_enabled = config.sound_enabled
        original_muted = config.muted
        try:
            config.sound_enabled = True
            config.muted = True  # App is muted
            player = SoundPlayer()

            with patch.object(player, "_play_sound_always") as mock_play:
                # These should NOT play when muted
                player.play_chat_sound()
                player.play_urgent_sound()

                mock_play.assert_not_called()
        finally:
            config.sound_enabled = original_enabled
            config.muted = original_muted

    def test_mute_feedback_sounds_play_when_muted(self):
        """Test that mute/unmute feedback sounds play regardless of mute state.

        The muted/unmuted audio feedback should always play so the user
        knows the state changed.
        """
        original_enabled = config.sound_enabled
        original_muted = config.muted
        try:
            config.sound_enabled = True
            config.muted = True  # Even when muted
            player = SoundPlayer()

            with patch.object(player, "_play_sound_always") as mock_play:
                # These SHOULD play even when muted
                player.play_muted_sound()
                player.play_unmuted_sound()

                assert mock_play.call_count == 2
        finally:
            config.sound_enabled = original_enabled
            config.muted = original_muted
