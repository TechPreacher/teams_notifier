"""
Setup script for building Teams Notifier as a macOS .app bundle.

Usage:
    python setup.py py2app
"""

import os
from setuptools import setup

APP = ['app_entry.py']
DATA_FILES = [
    ('resources/audio', [
        'resources/audio/GLaDOS-teams-message.wav',
        'resources/audio/GLaDOS-teams-urgent.wav',
    ]),
    ('src', []),  # Ensure src directory exists in bundle
]

# Check if custom icon exists
icon_file = 'resources/icon.icns' if os.path.exists('resources/icon.icns') else None

OPTIONS = {
    'argv_emulation': False,
    'iconfile': icon_file,
    'plist': {
        'CFBundleName': 'Teams Notifier',
        'CFBundleDisplayName': 'Teams Notifier',
        'CFBundleIdentifier': 'com.sascha.teams-notifier',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'LSMinimumSystemVersion': '11.0',
        'LSUIElement': False,  # Set to True to hide from Dock (menu bar only)
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    },
    'packages': [
        'nicegui',
        'pywebview',
        'uvicorn',
        'fastapi',
        'starlette',
        'objc',
        'Foundation',
        'src',
    ],
    'includes': [
        'src.config',
        'src.main',
        'src.ui',
        'src.ui.alert_window',
        'src.monitors',
        'src.monitors.notification_monitor',
        'src.audio',
        'src.audio.sound_player',
        'webview',
    ],
    'excludes': ['tkinter', 'matplotlib', 'scipy', 'numpy', 'pandas'],
    'resources': ['src', 'resources'],
}

setup(
    name='Teams Notifier',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
