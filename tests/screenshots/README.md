# TUI Screenshots & GIF Demos

此目录用于存放 TUI 界面的视觉素材。

## 待补充文件

| 文件 | 用途 | 文档引用 |
|------|------|---------|
| `tui-main.png` | TUI 主界面截图 | docs/tui-user-guide.md |
| `panels.png` | 三面板布局截图 | docs/tui-user-guide.md |
| `header.png` | Header 组件截图 | docs/tui-phase1-plan.md |
| `demo.gif` | 启动 + 操作演示 | README.md TUI 章节 |

## 制作方法

### 截图（推荐手动方式）

由于 WSL 环境限制，推荐使用手动截图：

```bash
# 1. 启动 TUI
cd ~/.openclaw/workspace/skills/lobster-doctor/scripts
python3 lobster_tui.py

# 2. 在 Windows 终端中使用系统截图工具
# - Windows: Win + Shift + S
# - macOS: Cmd + Shift + 4

# 3. 保存截图到此目录
# 文件名: tui-main.png, panels.png, header.png, demo.gif
```

### 自动截图（Linux 环境）

在原生 Linux 环境下可使用：

```bash
# 方法1：Textual 内置截图（需要交互环境）
textual run scripts/lobster_tui.py --screenshot tui-main.png

# 方法2：terminalizer 录制 GIF
terminalizer record -k lobster-tui-demo
terminalizer render lobster-tui-demo.yml -o demo.gif
```

## 临时占位符

在截图完成前，文档使用 ASCII 界面图展示 TUI 布局。

## 尺寸建议

| 图片类型 | 建议尺寸 | 格式 |
|---------|---------|------|
| 截图 | 1200x800 | PNG |
| GIF 演示 | 800x600 | GIF (<5MB) |

---

_创建时间：2026-04-02 | 状态：待填充_