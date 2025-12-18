"""macOS Menu Bar integration using rumps."""

import logging
import threading
import webbrowser
from typing import Callable

import rumps

from ..config import config

logger = logging.getLogger(__name__)


class TeamsMenuBar(rumps.App):
    """Menu bar app for Teams Notifier."""

    # Status icons (using emoji as simple icons)
    ICON_IDLE = "🟢"
    ICON_CHAT = "🟡"
    ICON_URGENT = "🔴"

    def __init__(self, port: int = 8080):
        super().__init__(
            name="Teams Alert",
            title=self.ICON_IDLE,
            quit_button=None,  # We'll add our own
        )

        self._port = port
        self._notification_count = 0
        self._show_window_callback: Callable | None = None
        self._quit_callback: Callable | None = None

        # Build menu
        self.menu = [
            rumps.MenuItem("Show Window", callback=self._show_window),
            rumps.MenuItem("Hide Window", callback=self._hide_window),
            None,  # Separator
            rumps.MenuItem("Reset Alerts", callback=self._reset_alerts),
            None,  # Separator
            rumps.MenuItem("Sound Enabled", callback=self._toggle_sound),
            None,  # Separator
            rumps.MenuItem("Quit", callback=self._quit_app),
        ]

        # Set initial state for sound toggle
        self.menu["Sound Enabled"].state = config.sound_enabled

    def set_show_window_callback(self, callback: Callable) -> None:
        """Set callback for showing the window."""
        self._show_window_callback = callback

    def set_quit_callback(self, callback: Callable) -> None:
        """Set callback for quitting the app."""
        self._quit_callback = callback

    def set_reset_callback(self, callback: Callable) -> None:
        """Set callback for resetting alerts."""
        self._reset_callback = callback

    def update_status(self, state: str, count: int = 0) -> None:
        """Update the menu bar icon and count."""
        self._notification_count = count

        if state == "idle":
            icon = self.ICON_IDLE
        elif state == "chat":
            icon = self.ICON_CHAT
        elif state == "urgent":
            icon = self.ICON_URGENT
        else:
            icon = self.ICON_IDLE

        # Show count if > 0
        if count > 0:
            self.title = f"{icon} {count}"
        else:
            self.title = icon

    def _show_window(self, sender) -> None:
        """Show the alert window."""
        webbrowser.open(f"http://localhost:{self._port}")

    def _hide_window(self, sender) -> None:
        """Hide the alert window (just a placeholder - NiceGUI windows can't be hidden)."""
        rumps.notification(
            title="Teams Alert",
            subtitle="",
            message="Close the browser window to hide the alert.",
        )

    def _reset_alerts(self, sender) -> None:
        """Reset all alerts."""
        if hasattr(self, "_reset_callback") and self._reset_callback:
            self._reset_callback()
        self.update_status("idle", 0)

    def _toggle_sound(self, sender) -> None:
        """Toggle sound on/off."""
        sender.state = not sender.state
        config.sound_enabled = sender.state

    def _quit_app(self, sender) -> None:
        """Quit the application."""
        if self._quit_callback:
            self._quit_callback()
        rumps.quit_application()


class MenuBarManager:
    """Manages the menu bar app in a separate thread."""

    def __init__(self, port: int = 8080):
        self._app: TeamsMenuBar | None = None
        self._thread: threading.Thread | None = None
        self._port = port

    def start(self) -> TeamsMenuBar:
        """Start the menu bar app in a background thread."""
        self._app = TeamsMenuBar(port=self._port)

        def run():
            self._app.run()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

        return self._app

    def stop(self) -> None:
        """Stop the menu bar app."""
        if self._app:
            rumps.quit_application()

    @property
    def app(self) -> TeamsMenuBar | None:
        """Get the menu bar app instance."""
        return self._app
