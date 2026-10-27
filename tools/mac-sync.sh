#!/bin/bash
# Download new CCP brief cards from GitHub into the Obsidian vault inbox.
# Each card is downloaded only once (ids recorded in ~/.ccp-sync/seen.txt),
# so moving, editing or deleting a card in the vault is never undone.
set -u
BASE="https://raw.githubusercontent.com/Haoxi-Z/ccp-brief-archive/main/cards"
DEST="${CCP_SYNC_DEST:-$HOME/Library/CloudStorage/OneDrive-Personal/04-obsidian/Haoxi/10-Work/11-CCP监管动态/_收件箱}"
DIR="$HOME/.ccp-sync"
STATE="$DIR/seen.txt"
LOG="$DIR/sync.log"
mkdir -p "$DIR"; touch "$STATE"
log() { echo "$(date '+%Y-%m-%d %H:%M') $*" >> "$LOG"; }

if ! mkdir -p "$DEST" 2>>"$LOG" || ! touch "$DEST/.ccp-sync-test" 2>>"$LOG"; then
  log "ERROR 无法写入 vault 收件箱：$DEST"
  exit 1
fi
rm -f "$DEST/.ccp-sync-test"

# Right after wake the network may not be up yet: keep trying for ~10 minutes.
idx=""
for i in $(seq 1 30); do
  idx=$(curl -fsSL -m 30 "$BASE/index.txt?t=$(date +%s)" 2>/dev/null) && break
  idx=""; sleep 20
done
if [ -z "$idx" ]; then
  log "ERROR 无法下载卡片列表（网络或 GitHub 不可用），一小时后自动重试"
  exit 1
fi

added=0
while IFS=$'\t' read -r id name; do
  [ -z "${id:-}" ] && continue
  grep -qx "$id" "$STATE" && continue
  tmp=$(mktemp)
  if curl -fsSL -m 30 --retry 3 --retry-delay 5 --retry-all-errors "$BASE/$id.md" -o "$tmp"; then
    if [ ! -e "$DEST/$name" ]; then
      mv "$tmp" "$DEST/$name" && added=$((added + 1))
    else
      rm -f "$tmp"
    fi
    echo "$id" >> "$STATE"
  else
    rm -f "$tmp"
    log "WARN 下载失败：$name"
  fi
done <<< "$idx"
log "OK 新增 $added 张卡片"
