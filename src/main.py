"""Main entry point for Teams Notifier."""

import asyncio
import logging
import signal
import sys

from nicegui import ui, app

from .config import config
from .monitors.notification_monitor import NotificationMonitor, NotificationType, TeamsNotification
from .audio.sound_player import SoundPlayer
from .ui.alert_window import AlertWindow, get_alert_window, AlertState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
monitor: NotificationMonitor | None = None
sound_player: SoundPlayer | None = None


def handle_notification(notification: TeamsNotification) -> None:
    """Handle incoming Teams notification."""
    alert = get_alert_window()
    
    if notification.type == NotificationType.CHAT:
        logger.info("Chat notification received")
        alert.notify_chat()
        if sound_player:
            sound_player.play_chat_sound()
    
    elif notification.type == NotificationType.MENTION:
        logger.info("Mention notification received")
        alert.notify_mention()
        if sound_player:
            sound_player.play_mention_sound()


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
    alert.build()


def run():
    """Run the Teams Notifier application."""
    global monitor, sound_player
    
    logger.info("Starting Teams Notifier...")
    
    # Set up signal handlers
    setup_signal_handlers()
    
    # Initialize components
    sound_player = SoundPlayer()
    
    # Start notification monitor
    monitor = NotificationMonitor()
    monitor.add_callback(handle_notification)
    monitor.start()
    
    port = 8080
    logger.info(f"Starting NiceGUI on port {port}...")
    
    # Note: Menu bar disabled due to thread conflicts with NiceGUI native mode
    # The alert window itself provides all necessary controls
    
    # Configure NiceGUI for small always-on-top window
    ui.run(
        port=port,
        title=config.window_title,
        reload=False,
        show=True,
        native=True,  # Use native window for always-on-top
        window_size=(config.window_width, config.window_height),
        frameless=False,
        fullscreen=False,
    )


def run_demo():
    """Run in demo mode with simulated notifications."""
    global sound_player
    
    logger.info("Starting Teams Notifier in DEMO mode...")
    
    sound_player = SoundPlayer()
    
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
            if random.random() < 0.3:  # 30% chance of mention
                logger.info("[DEMO] Simulating mention notification")
                alert.notify_mention()
                if sound_player:
                    sound_player.play_mention_sound()
            else:
                logger.info("[DEMO] Simulating chat notification")
                alert.notify_chat()
                if sound_player:
                    sound_player.play_chat_sound()
    
    @ui.page("/")
    def demo_page():
        alert = get_alert_window()
        alert.build()
        # Start simulation
        asyncio.create_task(simulate_notifications())
    
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
