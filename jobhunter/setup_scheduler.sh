#!/bin/bash
# setup_scheduler.sh — install launchd plist that runs JobHunter every 5 hours.
#
# Required env (set in your shell BEFORE running this script, e.g. in ~/.zshrc):
#   NTFY_TOPIC         — your secret ntfy.sh topic name (push notifications)
#   ANTHROPIC_API_KEY  — for LLM rerank + cover letters (optional but recommended)
#   CALLMEBOT_APIKEY   — optional WhatsApp fallback
#
# Phone is hardcoded below to the registered WhatsApp number.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/com.tabish.jobhunter.plist"
LOG_DIR="$SCRIPT_DIR/logs"

# Prefer the venv python so launchd-spawned runs have all deps (rich, httpx, pydantic, ...).
if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
  PYTHON="$SCRIPT_DIR/venv/bin/python"
else
  PYTHON=$(which python3)
  echo "⚠️  No venv found at $SCRIPT_DIR/venv. Falling back to $PYTHON."
  echo "   If you hit 'ModuleNotFoundError', run: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
fi

# Hard-coded WhatsApp number (international format, no +)
CALLMEBOT_PHONE_VALUE="923495447596"

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

  <!-- Every 5 hours = 18000 seconds. launchd will run on load and then every 5h. -->
  <key>StartInterval</key>
  <integer>18000</integer>

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
    <key>NTFY_TOPIC</key>
    <string>${NTFY_TOPIC:-}</string>
    <key>NTFY_SERVER</key>
    <string>${NTFY_SERVER:-https://ntfy.sh}</string>
    <key>CALLMEBOT_PHONE</key>
    <string>${CALLMEBOT_PHONE_VALUE}</string>
    <key>CALLMEBOT_APIKEY</key>
    <string>${CALLMEBOT_APIKEY:-}</string>
    <key>TELEGRAM_BOT_TOKEN</key>
    <string>${TELEGRAM_BOT_TOKEN:-}</string>
    <key>TELEGRAM_CHAT_ID</key>
    <string>${TELEGRAM_CHAT_ID:-}</string>
  </dict>

  <!-- Run once immediately after load so you get feedback. Subsequent runs follow StartInterval. -->
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
EOF

# Reload the plist
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "✅ JobHunter scheduler installed."
echo "   Runs every 5 hours (18000s)."
echo "   First run kicked off now (RunAtLoad=true)."
echo "   ntfy topic: ${NTFY_TOPIC:-NOT SET — push notifications will be skipped}"
echo "   Phone:      $CALLMEBOT_PHONE_VALUE"
echo "   WA key:     ${CALLMEBOT_APIKEY:+set}${CALLMEBOT_APIKEY:-NOT SET — WhatsApp will be skipped}"
echo "   Logs:       $LOG_DIR/jobhunter.log"
echo ""
echo "Commands:"
echo "  Run now:   launchctl start com.tabish.jobhunter"
echo "  Stop:      launchctl unload $PLIST_PATH"
echo "  Tail log:  tail -f $LOG_DIR/jobhunter.log"
