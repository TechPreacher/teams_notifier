# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Teams Notifier."""

import os
from pathlib import Path

block_cipher = None

# Get the project root
project_root = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['app_entry.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('resources/audio', 'resources/audio'),
    ],
    hiddenimports=[
        'nicegui',
        'webview',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'starlette',
        'objc',
        'Foundation',
        'AppKit',
        'PyObjCTools',
        'src',
        'src.config',
        'src.main',
        'src.ui',
        'src.ui.alert_window',
        'src.monitors',
        'src.monitors.notification_monitor',
        'src.audio',
        'src.audio.sound_player',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Teams Notifier',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Teams Notifier',
)

app = BUNDLE(
    coll,
    name='Teams Notifier.app',
    icon='resources/icon.icns',
    bundle_identifier='com.sascha.teams-notifier',
    info_plist={
        'CFBundleName': 'Teams Notifier',
        'CFBundleDisplayName': 'Teams Notifier',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'LSMinimumSystemVersion': '11.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
