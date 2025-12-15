#!/bin/bash
# Build Teams Notifier as a macOS .app bundle
set -e

cd "$(dirname "$0")"

echo "🔨 Building Teams Notifier.app..."
source .venv/bin/activate
pyinstaller TeamsNotifier.spec --noconfirm

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 App location: dist/Teams Notifier.app"
echo ""
echo "To install:"
echo "  cp -r 'dist/Teams Notifier.app' /Applications/"
echo ""
echo "To run:"
echo "  open 'dist/Teams Notifier.app'"
