# ccp-brief-archive

CCP 日报归档网页：https://haoxi-z.github.io/ccp-brief-archive/

- `index.html`：每天由 CCP 日报定时任务更新。
- `cards/`：由 GitHub Actions（`.github/workflows/cards.yml`）根据 `index.html` 自动生成的 Obsidian 新闻卡片，每条动态一张；`cards/index.txt` 是卡片清单。不要手动修改。
- `tools/build_cards.py`：生成卡片的脚本，议题和法域的对应关系也在这里调整。
- `tools/mac-sync.sh`、`tools/install-mac-sync.sh`：Mac 端每天 08:15（之后每小时补跑一次，刚唤醒没网时会等待重试）把新卡片下载到 vault 的 `10-Work/11-CCP监管动态/_收件箱`。每张卡片只下载一次，在 vault 里移动、修改或删除都不会被覆盖。

Mac 端安装（只需一次，在“终端”里运行）：

```
curl -fsSL https://raw.githubusercontent.com/Haoxi-Z/ccp-brief-archive/main/tools/install-mac-sync.sh | bash
```

查看同步记录：`tail ~/.ccp-sync/sync.log`

卸载：

```
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.haoxi.ccp-sync.plist; rm -rf ~/.ccp-sync ~/Library/LaunchAgents/com.haoxi.ccp-sync.plist
```
