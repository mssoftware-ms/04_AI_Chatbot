#!/bin/bash
# WSL Browser Installation Script

echo "🐧 WSL Browser Installation for WhatsApp AI Chatbot"
echo "=================================================="

# Check if we can use sudo
if sudo -n true 2>/dev/null; then
    echo "✅ Sudo access available"
else
    echo "⚠️  Sudo password required - run manually:"
    echo "   sudo apt update"
    echo "   sudo apt install -y chromium-browser"
    echo "   # OR"
    echo "   sudo apt install -y firefox"
    exit 1
fi

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Check what's available
echo "🔍 Checking available browsers..."

# Try to install Chromium first (lighter)
if apt list chromium-browser 2>/dev/null | grep -q chromium; then
    echo "🌐 Installing Chromium browser..."
    sudo apt install -y chromium-browser
    BROWSER="chromium-browser"
elif apt list firefox 2>/dev/null | grep -q firefox; then
    echo "🦊 Installing Firefox browser..."
    sudo apt install -y firefox
    BROWSER="firefox"
else
    echo "❌ No suitable browser found in repos"
    exit 1
fi

# Check if installation worked
if which $BROWSER >/dev/null 2>&1; then
    echo "✅ Browser installed: $BROWSER"
    
    # Test if we have display
    if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
        echo "✅ Display available: $DISPLAY$WAYLAND_DISPLAY"
        echo "🎉 Browser should work with Flet!"
    else
        echo "⚠️  No display detected"
        echo "💡 You may need to install WSLg or configure X11 forwarding"
    fi
else
    echo "❌ Browser installation failed"
    exit 1
fi

echo ""
echo "🎯 Next steps:"
echo "1. Run: python start_wsl_friendly.py full"
echo "2. Browser should open automatically now!"
echo "3. If not, manually open: http://localhost:8550"