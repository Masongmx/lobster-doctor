# TUI Section Template for README.md

> 此文件为 README.md TUI 章节的模板，待 developer 完成开发后集成

---

## 🖥️ TUI (Terminal User Interface)

<!-- INSERT POINT: 在 README.md 的 "What's New" 章节后插入 -->

### Quick Start

```bash
# Launch the TUI
python3 scripts/lobster_tui.py
```

<!-- TODO: 添加 GIF 演示 -->

### Interface Overview

<!-- TODO: 添加界面截图 -->

```
┌─────────────────────────────────────────────────────────────┐
│  🦞 Lobster Doctor    🟢 Healthy    128MB    12 folders     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌── Sessions ──┐  ┌── Files ──┐  ┌── Skills ──┐           │
│  │  ████░ 45%   │  │  temp/    │  │  skill A   │           │
│  │  ██░░░ 30%   │  │  cache/   │  │  skill B   │           │
│  │  ...         │  │  ...      │  │  ...       │           │
│  └──────────────┘  └───────────┘  └────────────┘           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  [A]rchive  [S]lim  [C]leanup  [H]ealth  [R]efresh  [Q]uit │
└─────────────────────────────────────────────────────────────┘
```

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `A` | Archive | Archive old memories |
| `S` | Slim | Trim skill descriptions |
| `C` | Cleanup | Safe cleanup of obsolete files |
| `H` | Health | Run comprehensive health check |
| `R` | Refresh | Manual refresh |
| `Q` | Quit | Exit TUI safely |

### Health Status Colors

| Icon | Workspace Size | Status |
|------|----------------|--------|
| 🟢 | < 500MB | Healthy |
| 🟡 | 500MB - 1GB | Attention |
| 🔴 | > 1GB | Danger |

### Features

- **Real-time Monitoring** — 5-second auto-refresh
- **Three-panel Layout** — Sessions, Files, Skills
- **One-key Actions** — Trigger commands instantly
- **Confirmation Dialogs** — Prevent accidental operations
- **Color-coded Status** — Visual health indicators

### Requirements

- Python >= 3.8
- `textual` and `rich` packages
- Terminal with UTF-8 and true color support

```bash
pip install textual rich
```

### Detailed Guide

See [TUI User Guide](docs/tui-user-guide.md) for:
- Full keyboard reference
- Configuration options
- Troubleshooting guide

---

<!-- END INSERT POINT -->

## Integration Instructions for developer

When TUI development is complete, integrate this section into README.md:

1. Locate the "What's New" section in README.md
2. Insert this section after "What's New" and before "Commands Reference"
3. Replace TODO placeholders with actual content:
   - Add GIF demo (use `terminalizer` or `asciinema`)
   - Add screenshots (save to `docs/images/`)
   - Update installation instructions if needed
4. Remove this template file after integration