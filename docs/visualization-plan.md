# 🦞 龙虾医生可视化模块设计方案

> 装得下，用得久，清得掉 — 从命令行到交互式 TUI

---

## 1. 设计目标

将现有的纯文本输出升级为交互式 Terminal UI（TUI），提供：
- **实时监控**：workspace 状态实时刷新
- **可视化呈现**：进度条、颜色标记、面板布局
- **交互式操作**：菜单选择、快捷键执行

---

## 2. 技术栈选择

### 推荐方案：Textual + Rich

| 库 | 作用 | 选择理由 |
|---|---|---|
| **Textual** | TUI 框架 | 完整的交互组件、布局系统、事件处理 |
| **Rich** | 渲染引擎 | 进度条、表格、颜色（Textual 内置） |

### 对比分析

| 库 | 交互性 | 学习成本 | 适用场景 |
|---|---|---|---|
| **Rich** | ❌ 无交互 | 低 | 美化输出、单次报告 |
| **Textual** | ✅ 完整交互 | 中 | 实时监控、交互式操作 |
| **Blessed** | ✅ 原始交互 | 高 | 精细终端控制 |

**结论**：Textual 最适合龙虾医生的需求（实时刷新 + 交互菜单 + 多面板布局）。

---

## 3. 参考 CLI 项目设计

### 3.1 htop（进程监控）

**学习点**：
- 上部概览 + 下部详情的垂直布局
- 颜色标记状态（🟢运行 🟡睡眠 🔴停止）
- 实时刷新（每秒更新）
- F键快捷操作栏

**应用到龙虾医生**：
- Header 显示 workspace 概览
- 实时刷新会话/文件状态
- 快捷键执行清理操作

### 3.2 duf（磁盘可视化）

**学习点**：
- 进度条显示磁盘占用率
- 颜色标记健康状态
- 表格展示分区信息
- 可交互排序

**应用到龙虾医生**：
- 进度条显示 token 占用率（相对阈值）
- 颜色标记健康状态（🟢🟡⚠️🔴）
- 表格展示会话/技能列表

### 3.3 lazygit（Git TUI）

**学习点**：
- 分面板布局（状态/详情/操作）
- 快捷键驱动操作
- 实时刷新 Git 状态

**应用到龙虾医生**：
- 三面板布局（Session/Files/Skills）
- 快捷键执行 archive/slim/cleanup

### 3.4 broot（文件树）

**学习点**：
- 文件树可视化浏览
- 搜索过滤
- 交互式选择

**应用到龙虾医生**：
- 可选：废弃文件树视图（Phase 2）

---

## 4. 界面布局设计

### 4.1 整体布局

```
┌─────────────────────────────────────────────────────────────────┐
│ 🦞 Lobster Doctor v4.0 │ workspace: 256MB │ hidden: 12 │ 🟢 健康 │
├───────────────────┬───────────────────┬─────────────────────────┤
│                   │                   │                         │
│  Session Monitor  │   Files Status    │    Skills Info          │
│                   │                   │                         │
│  ┌─────────────┐  │  ┌─────────────┐  │  ┌─────────────────────┐│
│  │ Total: 85K  │  │  │ Stale: 15   │  │  │ Skills: 73          ││
│  │ tokens      │  │  │ files       │  │  │                     ││
│  │             │  │  │             │  │  │ Desc: 2.1K tokens   ││
│  │ ████████░░  │  │  │ Violations: │  │  │                     ││
│  │ 65% used    │  │  │ 3 items     │  │  │ Top 5:              ││
│  │             │  │  │             │  │  │ • baoyu-*: 800      ││
│  │ Danger: 2   │  │  │ • archive   │  │  │ • lark-*: 600       ││
│  │ Warn: 5     │  │  │   misplaced │  │  │ • ...                ││
│  │             │  │  │ • node_mods │  │  │                     ││
│  │ [Detail]    │  │  │             │  │  │ [Slim]              ││
│  └─────────────┘  │  └─────────────┘  │  └─────────────────────┘│
│                   │                   │                         │
├───────────────────┴───────────────────┴─────────────────────────┤
│ [A] Archive  [S] Slim  [C] Cleanup  [H] Health  [R] Refresh  [Q] Quit │
│                                                                 │
│ Selected: Archive — 归档超过30天的记忆                          │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 组件详解

#### Header（顶部概览）

```python
# Textual Header widget
class LobsterHeader(Header):
    def __init__(self):
        self.title = "🦞 Lobster Doctor v4.0"
        self.workspace_size = "256MB"
        self.hidden_folders = 12
        self.health_status = "🟢"  # 或 🟡⚠️🔴
    
    def render(self):
        return f"{self.title} │ workspace: {self.workspace_size} │ hidden: {self.hidden_folders} │ {self.health_status} 健康"
```

#### Session Panel（左侧）

- **Total Tokens**：总 token 数 + 相对阈值百分比
- **Progress Bar**：Rich 进度条，颜色随阈值变化
- **Danger/Warn Count**：危险/警告会话数
- **Detail 按钮**：展开会话列表

```python
# Rich Progress Bar
from rich.progress import Progress, BarColumn

progress = Progress(
    "[progress.description]{task.description}",
    BarColumn(bar_width=40, complete_style="green", finished_style="yellow"),
    "[progress.percentage]{task.percentage:>3}%",
)

# 阈值颜色映射
threshold_colors = {
    "healthy": "green",    # < 50%
    "notice": "blue",      # 50-70%
    "warning": "yellow",   # 70-85%
    "danger": "red",       # > 85%
}
```

#### Files Panel（中间）

- **Stale Files**：废弃文件数 + 大小
- **Violations**：违规项列表（可折叠）
- **Cleanup 按钮**：执行清理

```python
# Textual DataTable
from textual.widgets import DataTable

files_table = DataTable()
files_table.add_columns("类型", "数量", "大小", "状态")
files_table.add_row("废弃脚本", "15", "2.3MB", "🟡")
files_table.add_row("临时文件", "8", "512KB", "🟢")
files_table.add_row("过期日志", "23", "1.1MB", "⚠️")
```

#### Skills Panel（右侧）

- **Total Skills**：技能总数
- **Description Tokens**：总 description token 数
- **Top 5**：token 占用最多的技能
- **Slim 按钮**：执行瘦身

#### Action Panel（底部）

- **快捷键菜单**：横向按钮栏
- **选中项说明**：当前选中操作的说明
- **执行反馈**：操作后的结果显示

---

## 5. 颜色标记规范

### 5.1 健康状态颜色

| 状态 | 占用 | 颜色 | Rich 样式 |
|---|---|---|---|
| 🟢 健康 | < 50% | 绿色 | `"green"` |
| 🔵 注意 | 50-70% | 蓝色 | `"blue"` |
| 🟡 警告 | 70-85% | 黄色 | `"yellow"` |
| 🔴 危险 | > 85% | 红色 | `"red"` |

### 5.2 应用场景

```python
# Token 占用进度条
if percentage < 50:
    color = "green"
elif percentage < 70:
    color = "blue"
elif percentage < 85:
    color = "yellow"
else:
    color = "red"

progress.add_task("Token Usage", total=100, completed=percentage, 
                  complete_style=color)
```

```python
# 会话列表颜色标记
for session in sessions:
    if session["tokens"] > danger_threshold:
        style = "bold red"
    elif session["tokens"] > warn_threshold:
        style = "yellow"
    else:
        style = "green"
    
    table.add_row(session["id"], session["agent"], 
                  f"{session['tokens']} tokens", style=style)
```

---

## 6. 交互设计

### 6.1 快捷键映射

| 快捷键 | 操作 | 说明 |
|---|---|---|
| `A` | Archive | 归档超过 N 天的记忆 |
| `S` | Slim | 技能瘦身 |
| `C` | Cleanup | 安全清理 |
| `H` | Health | 健康检查 |
| `R` | Refresh | 手动刷新数据 |
| `Q` | Quit | 退出 TUI |
| `?` | Help | 显示帮助 |
| `Enter` | Execute | 执行选中操作 |
| `↑↓` | Navigate | 切换菜单选项 |
| `Tab` | Switch Panel | 切换面板焦点 |
| `Esc` | Cancel | 取消当前操作 |

### 6.2 交互流程

```
启动 TUI
    │
    ├─ 自动刷新（每 5s）
    │   └─ 更新 Header + 各 Panel
    │
    ├─ 用户操作
    │   ├─ 按 A → 显示 Archive 确认对话框
    │   │   ├─ Enter → 执行 archive
    │   │   └─ Esc → 取消
    │   │
    │   ├─ 按 C → 显示 Cleanup 确认对话框
    │   │   ├─ Enter → 执行 cleanup
    │   │   └─ Esc → 取消
    │   │
    │   ├─ 按 R → 手动刷新
    │   │
    │   └─ 按 Q → 退出确认
    │       ├─ Enter → 退出
    │       └─ Esc → 继续运行
    │
    └─ 操作完成后
        └─ 显示结果 Toast（3s 后消失）
        └─ 自动刷新更新数据
```

### 6.3 确认对话框设计

```
┌─────────────────────────────────────┐
│  ⚠️ 确认执行 Archive 操作？         │
│                                     │
│  将归档超过 30 天未修改的记忆        │
│  预计节省 ~15K tokens               │
│                                     │
│  [Enter] 执行    [Esc] 取消         │
└─────────────────────────────────────┘
```

---

## 7. 实时刷新机制

### 7.1 刷新策略

| 场景 | 刷新频率 | 触发方式 |
|---|---|---|
| **自动刷新** | 5 秒 | 定时器 |
| **手动刷新** | 立即 | 按 R |
| **操作后刷新** | 立即 | 操作完成触发 |
| **首次加载** | 立即 | 启动时 |

### 7.2 Textual 定时器实现

```python
from textual.app import App
from textual.reactive import reactive

class LobsterDoctorApp(App):
    # Reactive 属性（自动更新 UI）
    workspace_size: reactive[str] = reactive("0MB")
    hidden_folders: reactive[int] = reactive(0)
    health_status: reactive[str] = reactive("🟢")
    
    def on_mount(self):
        """启动时设置定时器"""
        self.set_interval(5, self.refresh_data)
        self.refresh_data()  # 首次加载
    
    def refresh_data(self):
        """刷新所有数据"""
        # 调用 lobster_doctor.py 的函数获取数据
        health_data = cmd_health(json_output=True)
        
        # 更新 Reactive 属性
        self.workspace_size = fmt_size(health_data["files"]["stale_size"])
        self.hidden_folders = len(health_data.get("hidden_folders", []))
        
        # 根据阈值更新健康状态
        threshold = health_data["sessions"]["relative_threshold"]
        status_icons = {
            "healthy": "🟢",
            "notice": "🔵",
            "warning": "🟡",
            "danger": "🔴"
        }
        self.health_status = status_icons.get(threshold["status"], "⚪")
        
        # 更新各 Panel
        self.update_session_panel(health_data["sessions"])
        self.update_files_panel(health_data["files"])
        self.update_skills_panel(health_data["skills"])
```

---

## 8. 模块结构设计

### 8.1 文件结构

```
skills/lobster-doctor/
├── scripts/
│   ├── lobster_doctor.py      # 核心逻辑（现有）
│   ├── lobster_tui.py         # TUI 入口（新增）
│   └── tui/
│       ├── __init__.py
│       ├── app.py             # Textual App 主类
│       ├── widgets/
│       │   ├── __init__.py
│       │   ├── header.py      # Header 组件
│       │   ├── session_panel.py
│       │   ├── files_panel.py
│       │   ├── skills_panel.py
│       │   ├── action_bar.py  # 底部操作栏
│       │   └── confirm_dialog.py
│       └── styles/
│           └── lobster.css    # Textual CSS 样式
├── docs/
│   └── visualization-plan.md  # 本文档
└── tests/
    └── test_tui.py            # TUI 测试
```

### 8.2 核心类设计

```python
# lobster_tui.py（入口文件）
#!/usr/bin/env python3
"""
🦞 Lobster Doctor TUI — 交互式健康监控
"""

import sys
from pathlib import Path

# 导入 TUI App
sys.path.insert(0, str(Path(__file__).parent / "tui"))
from app import LobsterDoctorApp

def main():
    app = LobsterDoctorApp()
    app.run()

if __name__ == "__main__":
    main()
```

```python
# tui/app.py（主 App 类）
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import Container, Horizontal

from .widgets import (
    LobsterHeader,
    SessionPanel,
    FilesPanel,
    SkillsPanel,
    ActionBar,
)

class LobsterDoctorApp(App):
    """龙虾医生交互式 TUI"""
    
    CSS_PATH = "styles/lobster.css"
    BINDINGS = [
        ("a", "archive", "Archive"),
        ("s", "slim", "Slim"),
        ("c", "cleanup", "Cleanup"),
        ("h", "health", "Health"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
    ]
    
    def compose(self) -> ComposeResult:
        """构建 UI 组件"""
        yield LobsterHeader()
        yield Container(
            Horizontal(
                SessionPanel(),
                FilesPanel(),
                SkillsPanel(),
            ),
        )
        yield ActionBar()
        yield Footer()
    
    def action_archive(self):
        """执行 Archive 操作"""
        self.show_confirm_dialog("archive")
    
    def action_cleanup(self):
        """执行 Cleanup 操作"""
        self.show_confirm_dialog("cleanup")
    
    def action_refresh(self):
        """手动刷新"""
        self.refresh_data()
    
    def show_confirm_dialog(self, action):
        """显示确认对话框"""
        # 实现确认对话框逻辑
        ...
```

---

## 9. 样式设计（Textual CSS）

### 9.1 lobster.css

```css
/* 基础样式 */
LobsterDoctorApp {
    background: $surface;
    color: $text;
}

/* Header 样式 */
LobsterHeader {
    background: $primary;
    color: $text-on-primary;
    padding: 1 2;
    text-align: center;
}

/* Panel 样式 */
SessionPanel, FilesPanel, SkillsPanel {
    background: $panel;
    border: solid $primary;
    padding: 1 2;
    width: 1fr;
}

SessionPanel {
    border-title: "Session Monitor";
}

FilesPanel {
    border-title: "Files Status";
}

SkillsPanel {
    border-title: "Skills Info";
}

/* 进度条样式 */
ProgressBar {
    height: 2;
    complete-style: green;
    finished-style: yellow;
}

/* 状态颜色 */
.status-healthy {
    color: green;
}

.status-notice {
    color: blue;
}

.status-warning {
    color: yellow;
}

.status-danger {
    color: red;
    text-style: bold;
}

/* Action Bar 样式 */
ActionBar {
    background: $primary-darken-2;
    padding: 1 2;
    height: auto;
}

ActionButton {
    margin: 0 1;
    min-width: 10;
}

ActionButton:focus {
    background: $accent;
}

/* 确认对话框样式 */
ConfirmDialog {
    background: $surface-darken-2;
    border: thick $primary;
    padding: 2 4;
    align: center middle;
}
```

---

## 10. Phase 规划

### Phase 1：基础 TUI（MVP）

**目标**：最小可用版本，支持基本监控和操作

**交付项**：
- Header 显示 workspace 概览
- Session Panel 显示 token 占用进度条
- Files Panel 显示废弃文件统计
- Skills Panel 显示技能 token 数
- ActionBar 快捷键操作
- Archive/Cleanup 确认对话框
- 自动刷新（5s）

**预计工作量**：~200 行代码，2-3 天

### Phase 2：增强交互

**目标**：增加详情视图和更多交互

**交付项**：
- Session 详情视图（点击展开会话列表）
- Files 详情视图（废弃文件树）
- Skills 详情视图（技能列表 + 瘦身建议）
- 支持 --dry-run 模式预览
- 操作结果显示 Toast

**预计工作量**：~150 行代码，1-2 天

### Phase 3：高级功能

**目标**：增加历史趋势和预测功能

**交付项**：
- Token 占用趋势图（最近 7 天）
- 达到阈值的预测时间
- 会话压缩建议（哪些会话可以压缩）
- 配置面板（修改阈值、刷新频率）

**预计工作量**：~100 行代码，1-2 天

---

## 11. 与现有代码的集成

### 11.1 调用现有函数

TUI 不重新实现核心逻辑，而是调用 `lobster_doctor.py` 的现有函数：

```python
# tui/app.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lobster_doctor import (
    cmd_health,
    cmd_archive,
    cmd_cleanup,
    cmd_slim,
    cmd_session,
    cmd_system_health,
    calculate_relative_threshold,
    fmt_size,
    fmt_tokens,
)

class LobsterDoctorApp(App):
    def refresh_data(self):
        # 调用现有函数获取数据
        health_result = cmd_health(json_output=True)
        
        # 解析数据并更新 UI
        ...
```

### 11.2 新增命令入口

在 `lobster_doctor.py` 的 main() 中新增：

```python
# lobster_doctor.py
def main():
    parser = argparse.ArgumentParser(...)
    subparsers = parser.add_subparsers(dest="command")
    
    # ... 现有命令 ...
    
    # 新增 tui 命令
    tui_parser = subparsers.add_parser("tui", help="交互式 TUI 监控")
    
    args = parser.parse_args()
    
    if args.command == "tui":
        # 启动 TUI
        from tui.app import LobsterDoctorApp
        app = LobsterDoctorApp()
        app.run()
        return
    
    # ... 其他命令处理 ...
```

### 11.3 启动方式

```bash
# 方式 1：新增 tui 命令
python3 scripts/lobster_doctor.py tui

# 方式 2：直接运行 TUI 脚本
python3 scripts/lobster_tui.py

# 方式 3：SKILL.md 中添加命令映射
# （在 SKILL.md 的命令表中新增）
# | **tui** | ✨ 交互式 TUI 监控 |
```

---

## 12. 依赖管理

### 12.1 新增依赖

```json
// package.json
{
  "dependencies": {
    "textual": "^0.47.0",
    "rich": "^13.7.0"
  }
}
```

### 12.2 安装方式

```bash
# pip 安装
pip install textual rich

# 或在 lobster-doctor 的 package.json 中声明
# 由 OpenClaw 自动安装
```

---

## 13. 测试策略

### 13.1 单元测试

```python
# tests/test_tui.py
import pytest
from textual.pilot import Pilot

from tui.app import LobsterDoctorApp

@pytest.fixture
async def app():
    app = LobsterDoctorApp()
    async with app.run_test() as pilot:
        yield pilot

async def test_refresh_data(app: Pilot):
    """测试数据刷新"""
    # 检查 Header 是否更新
    header = app.app.query_one("LobsterHeader")
    assert header.workspace_size != "0MB"

async def test_archive_action(app: Pilot):
    """测试 Archive 操作"""
    # 按 A
    await app.press("a")
    
    # 检查确认对话框是否显示
    dialog = app.app.query_one("ConfirmDialog")
    assert dialog.visible

async def test_colors(app: Pilot):
    """测试颜色标记"""
    # 模拟不同阈值状态
    # 检查颜色是否正确映射
    ...
```

### 13.2 手动测试清单

| 测试项 | 检查点 |
|---|---|
| **启动** | TUI 正常显示，数据加载成功 |
| **刷新** | 自动刷新（5s），手动刷新（R） |
| **颜色** | 不同阈值显示正确颜色 |
| **交互** | 快捷键响应正确 |
| **操作** | Archive/Cleanup 执行成功 |
| **退出** | Q 正常退出，数据保存 |

---

## 14. 用户文档

### 14.1 快速开始

```bash
# 启动 TUI
python3 scripts/lobster_doctor.py tui

# 或
python3 scripts/lobster_tui.py
```

### 14.2 界面说明

- **顶部**：workspace 概览（大小、隐藏文件夹数、健康状态）
- **左侧面板**：Session 监控（token 占用、进度条、危险会话数）
- **中间面板**：Files 状态（废弃文件、违规项）
- **右侧面板**：Skills 信息（技能数、description token 数）
- **底部**：快捷键操作栏

### 14.3 快捷键

按 `?` 显示帮助，或参考本文档第 6.1 节。

---

## 15. 总结

### 核心价值

- **装得下** → 可视化技能瘦身建议
- **用得久** → 实时监控 token 占用，相对阈值告警
- **清得掉** → 交互式清理菜单，确认对话框保护

### 技术亮点

- **不重复造轮子**：使用 Textual + Rich 现成组件
- **分离关注点**：TUI 仅负责 UI，核心逻辑复用 lobster_doctor.py
- **渐进式开发**：Phase 1 MVP → Phase 2 增强 → Phase 3 高级

### 预计效果

- 从纯文本输出升级为交互式 TUI
- 实时监控 workspace 健康状态
- 降低误操作风险（确认对话框）
- 提升用户体验（颜色标记、进度条、快捷键）

---

## 附录：参考资料

### CLI TUI 项目

| 项目 | GitHub | 学习点 |
|---|---|---|
| htop | https://github.com/htop-dev/htop | 进程监控、实时刷新 |
| duf | https://github.com/muesli/duf | 磁盘可视化、进度条 |
| lazygit | https://github.com/jesseduffield/lazygit | Git TUI、分面板布局 |
| broot | https://github.com/Canop/broot | 文件树、交互式选择 |

### Python TUI 库

| 库 | 文档 | 适用场景 |
|---|---|---|
| Textual | https://textual.textualize.io/ | 完整 TUI 应用 |
| Rich | https://rich.readthedocs.io/ | 美化输出、进度条 |
| Blessed | https://blessed.readthedocs.io/ | 精细终端控制 |

---

**设计完成，等待老板确认后进入 Phase 1 开发。** 🫡