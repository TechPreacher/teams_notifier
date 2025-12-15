# Teams Notifier 🚨

A macOS alert light application that monitors Microsoft Teams for new chat messages and mentions, providing visual and audio notifications.

## Features

- **Visual Alert Light** - A small, always-on-top window that looks like an alert light
  - 🟢 **Green** = All clear, no pending notifications
  - 🟡 **Yellow (pulsing)** = New chat message
  - 🔴 **Red (flashing)** = You were mentioned
- **Notification Counter** - Shows the number of pending notifications
- **Sound Alerts** - Different sounds for chat vs mention notifications
- **Menu Bar Icon** - Quick access from the macOS menu bar
- **Reset Button** - Acknowledge notifications and return to idle state

## Requirements

- macOS 11.0 or later
- Python 3.11+
- Microsoft Teams (running in background)
- Teams notifications enabled in macOS System Settings

## Installation

1. **Clone the repository** (if you haven't already):
   ```bash
   cd /path/to/Teams/Notifier
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Grant permissions** (required for notification monitoring):
   - Go to **System Settings** → **Privacy & Security** → **Accessibility**
   - Add your terminal app (Terminal.app, iTerm, or VS Code)
   - Also check **Notifications** → Ensure Teams has notifications enabled

## Usage

### Normal Mode
Run the notifier to monitor Teams:
```bash
python -m src.main
```

### Demo Mode
Test the UI with simulated notifications:
```bash
python -m src.main --demo
```

## How It Works

The app monitors macOS Distributed Notification Center for Teams notifications. When Teams sends a notification to macOS, this app intercepts it and:

1. Determines if it's a chat message or mention
2. Updates the visual alert light
3. Plays the appropriate sound
4. Updates the notification count

## Configuration

Edit `src/config.py` to customize:

```python
# Window size
window_width: int = 150
window_height: int = 200

# Sounds (use any .aiff file from /System/Library/Sounds/)
chat_sound: str = "/System/Library/Sounds/Blow.aiff"
mention_sound: str = "/System/Library/Sounds/Glass.aiff"

# Animation speeds (seconds)
pulse_speed: float = 1.0   # Yellow pulsing
flash_speed: float = 0.3   # Red flashing

# Colors (CSS format)
color_idle: str = "#22c55e"    # Green
color_chat: str = "#eab308"    # Yellow  
color_mention: str = "#ef4444" # Red
```

### Available System Sounds

Run this to list available sounds:
```bash
ls /System/Library/Sounds/
```

Common options: `Basso.aiff`, `Blow.aiff`, `Bottle.aiff`, `Frog.aiff`, `Funk.aiff`, `Glass.aiff`, `Hero.aiff`, `Morse.aiff`, `Ping.aiff`, `Pop.aiff`, `Purr.aiff`, `Sosumi.aiff`, `Submarine.aiff`, `Tink.aiff`

## Menu Bar

The app adds an icon to your menu bar:

- 🟢 / 🟡 / 🔴 - Status indicator with count
- **Show Window** - Open the alert light in browser
- **Reset Alerts** - Clear all notifications
- **Sound Enabled** - Toggle sound on/off
- **Quit** - Exit the application

## Troubleshooting

### Notifications not detected

1. **Check Teams notifications are enabled**:
   - macOS: System Settings → Notifications → Microsoft Teams → Allow Notifications
   - Teams: Settings → Notifications → Enable all relevant options

2. **Check accessibility permissions**:
   - System Settings → Privacy & Security → Accessibility
   - Ensure your terminal/Python is listed and checked

3. **Verify Teams is running**:
   - The app monitors notifications from Teams, so Teams must be running

### No sound

1. Check system volume is not muted
2. Verify sound files exist:
   ```bash
   ls /System/Library/Sounds/
   ```
3. Test sounds manually:
   ```bash
   afplay /System/Library/Sounds/Glass.aiff
   ```

### Window not staying on top

The native window mode may not work on all systems. Try running without native mode by editing `src/main.py` and setting `native=False` in `ui.run()`.

## Development

### Project Structure

```
src/
├── __init__.py
├── main.py              # Entry point
├── config.py            # Configuration settings
├── ui/
│   ├── __init__.py
│   ├── alert_window.py  # NiceGUI alert light UI
│   └── menu_bar.py      # macOS menu bar integration
├── monitors/
│   ├── __init__.py
│   └── notification_monitor.py  # macOS notification listener
└── audio/
    ├── __init__.py
    └── sound_player.py  # Sound playback
```

### Running Tests

```bash
pytest tests/
```

## License

MIT License - Feel free to modify and use as needed.
