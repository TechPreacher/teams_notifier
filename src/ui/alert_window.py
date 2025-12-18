"""NiceGUI Alert Light window component."""

import asyncio
import logging
import queue
from enum import Enum, auto

from nicegui import ui

from ..config import config

logger = logging.getLogger(__name__)


class AlertState(Enum):
    """Visual states for the alert light."""

    IDLE = auto()
    CHAT = auto()
    URGENT = auto()


class AlertWindow:
    """Alert light window using NiceGUI."""

    def __init__(self):
        self._state = AlertState.IDLE
        self._chat_count = 0
        self._urgent_count = 0
        self._light_element = None
        self._count_label = None
        self._status_label = None
        self._mute_button = None
        self._animation_task: asyncio.Task | None = None
        self._light_on = True
        self._muted = config.muted

        # Callbacks for external events
        self._on_reset_callbacks: list = []
        self._on_mute_callbacks: list = []

        # Thread-safe notification queue for cross-thread communication
        self._notification_queue: queue.Queue = queue.Queue()
        self._queue_processor_started = False

    @property
    def state(self) -> AlertState:
        """Current alert state."""
        return self._state

    @property
    def total_count(self) -> int:
        """Total notification count."""
        return self._chat_count + self._urgent_count

    @property
    def muted(self) -> bool:
        """Whether the app is muted."""
        return self._muted

    def on_reset(self, callback) -> None:
        """Register a callback for when reset is clicked.

        Clears any existing callbacks first to prevent duplicate calls.
        """
        self._on_reset_callbacks.clear()
        self._on_reset_callbacks.append(callback)

    def on_mute(self, callback) -> None:
        """Register a callback for when mute is toggled.

        Clears any existing callbacks first to prevent duplicate calls.
        """
        self._on_mute_callbacks.clear()
        self._on_mute_callbacks.append(callback)

    def notify_chat(self) -> None:
        """Register a new chat notification (thread-safe)."""
        # Queue the notification for processing in the main thread
        self._notification_queue.put(("chat", None))

    def notify_urgent(self) -> None:
        """Register a new urgent notification (thread-safe)."""
        # Queue the notification for processing in the main thread
        self._notification_queue.put(("urgent", None))

    def _process_chat(self) -> None:
        """Process a chat notification (must be called from main thread)."""
        self._chat_count += 1
        # Only upgrade to CHAT if not already in URGENT state
        if self._state == AlertState.IDLE:
            self._set_state(AlertState.CHAT)
        self._update_display()

    def _process_urgent(self) -> None:
        """Process an urgent notification (must be called from main thread)."""
        self._urgent_count += 1
        # URGENT always takes priority
        self._set_state(AlertState.URGENT)
        self._update_display()

    def reset(self) -> None:
        """Reset to idle state and clear counts."""
        self._chat_count = 0
        self._urgent_count = 0
        self._set_state(AlertState.IDLE)
        self._update_display()

        # Trigger callbacks
        for callback in self._on_reset_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Reset callback error: {e}")

    def toggle_mute(self) -> None:
        """Toggle mute state."""
        self._muted = not self._muted
        config.muted = self._muted
        self._update_display()
        self._update_mute_button()

        # Trigger callbacks
        for callback in self._on_mute_callbacks:
            try:
                callback(self._muted)
            except Exception as e:
                logger.error(f"Mute callback error: {e}")

    def _update_mute_button(self) -> None:
        """Update the mute button text."""
        if self._mute_button:
            if self._muted:
                self._mute_button.set_text("Unmute")
            else:
                self._mute_button.set_text("Mute")

    def _set_state(self, state: AlertState) -> None:
        """Set the alert state and update animation."""
        if self._state == state:
            return

        self._state = state
        self._start_animation()

    def _start_animation(self) -> None:
        """Start the appropriate animation for current state."""
        # Cancel existing animation
        if self._animation_task and not self._animation_task.done():
            self._animation_task.cancel()

        if self._state == AlertState.IDLE:
            # No animation, solid color
            self._light_on = True
            self._update_light_color()
        elif self._state == AlertState.CHAT:
            # Pulsing animation
            try:
                self._animation_task = asyncio.create_task(self._pulse_animation())
            except RuntimeError:
                # No event loop running (e.g., in tests)
                self._light_on = True
                self._update_light_color()
        elif self._state == AlertState.URGENT:
            # Flashing animation
            try:
                self._animation_task = asyncio.create_task(self._flash_animation())
            except RuntimeError:
                # No event loop running (e.g., in tests)
                self._light_on = True
                self._update_light_color()

    async def _pulse_animation(self) -> None:
        """Slow pulsing animation for chat notifications."""
        try:
            while self._state == AlertState.CHAT:
                self._light_on = not self._light_on
                self._update_light_color()
                await asyncio.sleep(config.pulse_speed)
        except asyncio.CancelledError:
            pass

    async def _flash_animation(self) -> None:
        """Fast flashing animation for urgent notifications."""
        try:
            while self._state == AlertState.URGENT:
                self._light_on = not self._light_on
                self._update_light_color()
                await asyncio.sleep(config.flash_speed)
        except asyncio.CancelledError:
            pass

    def _update_light_color(self) -> None:
        """Update the light element color."""
        if not self._light_element:
            return

        if self._muted:
            color = config.color_muted  # Dark blue when muted
        elif not self._light_on:
            color = "#374151"  # Dark gray (off)
        elif self._state == AlertState.IDLE:
            color = config.color_idle
        elif self._state == AlertState.CHAT:
            color = config.color_chat
        elif self._state == AlertState.URGENT:
            color = config.color_urgent
        else:
            color = config.color_idle

        self._light_element.style(f"background-color: {color}")

    def _update_display(self) -> None:
        """Update the display elements."""
        if self._count_label:
            count = self.total_count
            self._count_label.set_text(str(count) if count > 0 else "")

        if self._status_label:
            if self._muted:
                self._status_label.set_text("Muted")
            elif self._state == AlertState.IDLE:
                self._status_label.set_text("All Clear")
            elif self._state == AlertState.CHAT:
                self._status_label.set_text("New Chat!")
            elif self._state == AlertState.URGENT:
                self._status_label.set_text("Urgent!")

        self._update_light_color()

    def build(self) -> None:
        """Build the NiceGUI interface."""
        # Configure the page - set dark background on html and body to eliminate white borders
        ui.query("html").style("background-color: #1f2937;")
        ui.query("body").style(
            "margin: 0; padding: 0; overflow: hidden; background-color: #1f2937;"
        )

        # Main container
        with (
            ui.column()
            .classes("w-full h-screen items-center justify-center gap-2 p-2")
            .style(
                "background-color: #1f2937;"  # Dark background
            )
        ):
            # Alert light (circular)
            with (
                ui.element("div")
                .classes("relative rounded-full flex items-center justify-center")
                .style(
                    f"width: 100px; height: 100px; background-color: {config.color_idle}; "
                    "box-shadow: 0 0 20px rgba(34, 197, 94, 0.5); "
                    "transition: box-shadow 0.3s ease;"
                ) as light
            ):
                self._light_element = light

                # Count badge (inside the light)
                self._count_label = (
                    ui.label("")
                    .classes("text-2xl font-bold text-white")
                    .style("text-shadow: 0 0 10px rgba(0,0,0,0.5);")
                )

            # Status text
            self._status_label = ui.label(
                "Muted" if self._muted else "All Clear"
            ).classes("text-sm font-medium text-gray-300")

            # Mute button (above reset)
            self._mute_button = (
                ui.button(
                    "Unmute" if self._muted else "Mute", on_click=self.toggle_mute
                )
                .classes("mt-2")
                .props("dense size=sm color=blue-8")
            )

            # Reset button
            ui.button("Reset", on_click=self.reset).classes("mt-1").props(
                "dense size=sm color=grey-8"
            )

        # Update glow effect based on state
        self._setup_glow_updates()

    def _setup_glow_updates(self) -> None:
        """Set up dynamic glow effect updates."""

        async def update_glow():
            while True:
                if self._light_element:
                    if self._muted:
                        glow_color = "rgba(30, 58, 95, 0.5)"  # Dark blue glow
                    elif self._state == AlertState.IDLE:
                        glow_color = "rgba(34, 197, 94, 0.5)"
                    elif self._state == AlertState.CHAT:
                        glow_color = "rgba(234, 179, 8, 0.6)"
                    elif self._state == AlertState.URGENT:
                        glow_color = "rgba(239, 68, 68, 0.8)"
                    else:
                        glow_color = "rgba(34, 197, 94, 0.5)"

                    if self._muted or self._light_on:
                        self._light_element.style(f"box-shadow: 0 0 30px {glow_color};")
                    else:
                        self._light_element.style(
                            "box-shadow: 0 0 5px rgba(0,0,0,0.3);"
                        )

                await asyncio.sleep(0.1)

        asyncio.create_task(update_glow())

        # Start the notification queue processor
        self._start_queue_processor()

    def _start_queue_processor(self) -> None:
        """Start processing the notification queue in the main event loop."""
        if self._queue_processor_started:
            return
        self._queue_processor_started = True

        async def process_queue():
            """Process notifications from the queue."""
            while True:
                try:
                    # Check for queued notifications
                    while not self._notification_queue.empty():
                        try:
                            notification_type, _ = self._notification_queue.get_nowait()
                            if notification_type == "chat":
                                self._process_chat()
                            elif notification_type == "urgent":
                                self._process_urgent()
                        except queue.Empty:
                            break
                except Exception as e:
                    logger.error(f"Error processing notification queue: {e}")

                await asyncio.sleep(0.1)  # Check queue 10 times per second

        asyncio.create_task(process_queue())


# Global alert window instance
alert_window: AlertWindow | None = None


def get_alert_window() -> AlertWindow:
    """Get the global alert window instance."""
    global alert_window
    if alert_window is None:
        alert_window = AlertWindow()
    return alert_window
