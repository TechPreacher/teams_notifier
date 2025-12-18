#!/usr/bin/env python3
"""Entry point for the Teams Notifier application."""

import sys
import os

# Ensure the src package is importable when running as .app
if getattr(sys, "frozen", False):
    # Running as a bundled app
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(app_dir, "Resources"))
    os.chdir(os.path.join(app_dir, "Resources"))

from src.main import run

if __name__ == "__main__":
    run()
