"""Main entry point for Teams Notifier."""

import asyncio
import logging
import signal
import sys

# Configure logging FIRST, before any other imports that might create loggers
# Import config to load .env and get log level
from .config import config

# Get the log level from config
log_level = getattr(logging, config.log_level, logging.INFO)

# Configure root logger - use force=True to override any existing config
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)

# Also set level on the root logger explicitly
logging.getLogger().setLevel(log_level)

logger = logging.getLogger(__name__)

# Now import other modules (their loggers will inherit the configured level)
from nicegui import ui, app  # noqa: E402

from .monitors.log_stream_monitor import (  # noqa: E402
    LogStreamMonitor,
    NotificationType,
    TeamsNotification,
)
from .audio.sound_player import SoundPlayer  # noqa: E402
from .ui.alert_window import get_alert_window  # noqa: E402
from .webhook import WebhookSender  # noqa: E402

# Global instances
monitor: LogStreamMonitor | None = None
sound_player: SoundPlayer | None = None
webhook_sender: WebhookSender | None = None


def handle_notification(notification: TeamsNotification) -> None:
    """Handle incoming Teams notification."""
    alert = get_alert_window()

    if notification.type == NotificationType.CHAT:
        logger.info("Chat notification received")
        alert.notify_chat()
        if sound_player and not alert.muted:
            sound_player.play_chat_sound()
        if webhook_sender:
            webhook_sender.send_notification_sync("message")

    elif notification.type == NotificationType.URGENT:
        logger.info("Urgent notification received")
        alert.notify_urgent()
        if sound_player and not alert.muted:
            sound_player.play_urgent_sound()
        if webhook_sender:
            webhook_sender.send_notification_sync("urgent")


def setup_signal_handlers() -> None:
    """Set up graceful shutdown handlers."""

    def shutdown(signum, frame):
        logger.info("Shutting down...")
        if monitor:
            monitor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)


@ui.page("/")
def main_page():
    """Main page with the alert light."""
    alert = get_alert_window()

    # Register webhook callback for reset/clear button
    def on_reset():
        if webhook_sender:
            webhook_sender.send_notification_sync("clear")
            logger.info("Clear notification sent to webhook")

    # Register mute callback to play sounds
    def on_mute(muted: bool):
        if sound_player:
            if muted:
                sound_player.play_muted_sound()
            else:
                sound_player.play_unmuted_sound()
        logger.info(f"Mute state changed: {'muted' if muted else 'unmuted'}")

    alert.on_reset(on_reset)
    alert.on_mute(on_mute)
    alert.build()


async def set_always_on_top():
    """Set the window to always be on top after it's created."""
    await asyncio.sleep(1.5)  # Wait for window to be fully ready
    try:
        # Use pywebview's on_top property
        if app.native.main_window:
            app.native.main_window.on_top = True
            logger.info("Window set to always-on-top via pywebview")
    except Exception as e:
        logger.warning(f"Could not set always-on-top: {e}")

    # Periodically re-apply on_top to ensure it stays on top
    async def keep_on_top():
        while True:
            await asyncio.sleep(5.0)
            try:
                if app.native.main_window:
                    app.native.main_window.on_top = True
            except Exception:
                pass

    asyncio.create_task(keep_on_top())


def run():
    """Run the Teams Notifier application."""
    global monitor, sound_player, webhook_sender

    logger.info("Starting Teams Notifier...")

    # Set up signal handlers
    setup_signal_handlers()

    # Initialize components
    sound_player = SoundPlayer()
    webhook_sender = WebhookSender(
        webhook_url=config.webhook_url,
        payload_message=config.webhook_payload_message,
        payload_urgent=config.webhook_payload_urgent,
        payload_clear=config.webhook_payload_clear,
        bearer_token=config.webhook_bearer,
    )
    if webhook_sender.enabled:
        logger.info(f"Webhook notifications enabled: {config.webhook_url}")
        if config.webhook_bearer:
            logger.info("Webhook authorization: Bearer token configured")

    # Start notification monitor (uses log stream to detect Teams notifications)
    monitor = LogStreamMonitor()
    monitor.add_callback(handle_notification)
    monitor.start()

    port = 8080
    logger.info(f"Starting NiceGUI on port {port}...")

    # Note: Menu bar disabled due to thread conflicts with NiceGUI native mode
    # The alert window itself provides all necessary controls

    # Set always-on-top after startup
    app.on_startup(set_always_on_top)

    # Configure NiceGUI for small native window
    ui.run(
        port=port,
        title=config.window_title,
        reload=False,
        show=True,
        native=True,
        window_size=(config.window_width, config.window_height),
        frameless=False,
        fullscreen=False,
    )


def run_demo():
    """Run in demo mode with simulated notifications."""
    global sound_player, webhook_sender

    logger.info("Starting Teams Notifier in DEMO mode...")

    sound_player = SoundPlayer()
    webhook_sender = WebhookSender(
        webhook_url=config.webhook_url,
        payload_message=config.webhook_payload_message,
        payload_urgent=config.webhook_payload_urgent,
        payload_clear=config.webhook_payload_clear,
        bearer_token=config.webhook_bearer,
    )
    if webhook_sender.enabled:
        logger.info(f"Webhook notifications enabled: {config.webhook_url}")
        if config.webhook_bearer:
            logger.info("[DEMO] Webhook authorization: Bearer token configured")

    async def simulate_notifications():
        """Simulate notifications for testing."""
        import random

        await asyncio.sleep(3)  # Wait for UI to be ready

        alert = get_alert_window()

        while True:
            # Random delay between 5-15 seconds
            delay = random.uniform(5, 15)
            await asyncio.sleep(delay)

            # Random notification type
            if random.random() < 0.3:  # 30% chance of urgent
                logger.info("[DEMO] Simulating urgent notification")
                alert.notify_urgent()
                if sound_player and not alert.muted:
                    sound_player.play_urgent_sound()
                if webhook_sender:
                    webhook_sender.send_notification_sync("urgent")
            else:
                logger.info("[DEMO] Simulating chat notification")
                alert.notify_chat()
                if sound_player and not alert.muted:
                    sound_player.play_chat_sound()
                if webhook_sender:
                    webhook_sender.send_notification_sync("message")

    @ui.page("/")
    def demo_page():
        alert = get_alert_window()

        # Register webhook callback for reset/clear button
        def on_reset():
            if webhook_sender:
                webhook_sender.send_notification_sync("clear")
                logger.info("[DEMO] Clear notification sent to webhook")

        # Register mute callback to play sounds
        def on_mute(muted: bool):
            if sound_player:
                if muted:
                    sound_player.play_muted_sound()
                else:
                    sound_player.play_unmuted_sound()
            logger.info(f"[DEMO] Mute state changed: {'muted' if muted else 'unmuted'}")

        alert.on_reset(on_reset)
        alert.on_mute(on_mute)
        alert.build()
        # Start simulation
        asyncio.create_task(simulate_notifications())

    # Set always-on-top after startup
    app.on_startup(set_always_on_top)

    ui.run(
        port=8080,
        title=config.window_title + " [DEMO]",
        reload=False,
        show=True,
        native=True,
        window_size=(config.window_width, config.window_height),
    )


if __name__ == "__main__":
    # Check for demo mode
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_demo()
    else:
        run()
