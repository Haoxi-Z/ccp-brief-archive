#!/bin/bash
# One-time installer: copies mac-sync.sh to ~/.ccp-sync and schedules it daily
# at 08:15, at login and every hour after that. If the Mac is asleep at 08:15,
# it runs on wake. Re-runs are harmless: each card is downloaded only once.
# Uninstall:
#   launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.haoxi.ccp-sync.plist; rm -rf ~/.ccp-sync ~/Library/LaunchAgents/com.haoxi.ccp-sync.plist
set -eu
DIR="$HOME/.ccp-sync"
PLIST="$HOME/Library/LaunchAgents/com.haoxi.ccp-sync.plist"
LABEL="com.haoxi.ccp-sync"
mkdir -p "$DIR" "$HOME/Library/LaunchAgents"
curl -fsSL "https://raw.githubusercontent.com/Haoxi-Z/ccp-brief-archive/main/tools/mac-sync.sh?t=$(date +%s)" -o "$DIR/sync.sh"
chmod +x "$DIR/sync.sh"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$DIR/sync.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>15</integer></dict>
  <key>StartInterval</key><integer>3600</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>$DIR/launchd.err</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
sleep 8
echo "—— 安装完成。最近一次同步记录："
tail -n 3 "$DIR/sync.log" 2>/dev/null || echo "（还没有记录，稍后可运行：tail ~/.ccp-sync/sync.log）"
