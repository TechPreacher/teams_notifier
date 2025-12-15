#!/bin/bash
# Teams Notifier Launcher
cd "$(dirname "$0")"
source .venv/bin/activate
python -m src.main
