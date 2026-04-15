#!/bin/bash
# setup_scheduler.sh — install launchd plist to run JobHunter at 09:00 and 18:00 PKT (UTC+5)
# PKT 09:00 = UTC 04:00; PKT 18:00 = UTC 13:00

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/com.tabish.jobhunter.plist"
LOG_DIR="$SCRIPT_DIR/logs"
PYTHON=$(which python3)

mkdir -p "$LOG_DIR"
mkdir -p "$PLIST_DIR"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.tabish.jobhunter</string>

  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$SCRIPT_DIR/main.py</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$SCRIPT_DIR</string>

  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Hour</key><integer>4</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
    <dict>
      <key>Hour</key><integer>13</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
  </array>

  <key>StandardOutPath</key>
  <string>$LOG_DIR/jobhunter.log</string>

  <key>StandardErrorPath</key>
  <string>$LOG_DIR/jobhunter_error.log</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    <key>ANTHROPIC_API_KEY</key>
    <string>${ANTHROPIC_API_KEY:-}</string>
    <key>TELEGRAM_BOT_TOKEN</key>
    <string>${TELEGRAM_BOT_TOKEN:-}</string>
    <key>TELEGRAM_CHAT_ID</key>
    <string>${TELEGRAM_CHAT_ID:-}</string>
  </dict>

  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
EOF

# Load the plist
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "✅ JobHunter scheduler installed!"
echo "   Runs at: 09:00 PKT (04:00 UTC) and 18:00 PKT (13:00 UTC)"
echo "   Logs: $LOG_DIR/jobhunter.log"
echo ""
echo "Commands:"
echo "  Start now:  launchctl start com.tabish.jobhunter"
echo "  Stop:       launchctl unload $PLIST_PATH"
echo "  View log:   tail -f $LOG_DIR/jobhunter.log"
