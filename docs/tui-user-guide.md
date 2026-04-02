# 龙虾医生 TUI 用户指南

> **Terminal User Interface** — 终端可视化界面
> 
> 让 workspace 健康状况一目了然。

---

## 📖 目录

- [功能介绍](#功能介绍)
- [安装指南](#安装指南)
- [快速开始](#快速开始)
- [快捷键参考](#快捷键参考)
- [配置说明](#配置说明)
- [故障排查](#故障排查)

---

## 功能介绍

### 概述

龙虾医生 TUI 是一个基于 **Textual + Rich** 的终端可视化界面，实时监控 OpenClaw workspace 的健康状态。

<!-- 界面截图待补充 -->
<!-- ![TUI界面](tests/screenshots/tui-main.png) -->

### 核心功能

#### 1. 实时健康监控

| 指标 | 说明 | 当前示例 |
|------|------|---------|
| Workspace 大小 | 实时显示，颜色标记健康状态 | 16.7MB 🟢 |
| 隐藏文件夹 | 计数显示，方便清理 | 5 个 |
| Sessions 状态 | Token 占用进度条 | 3 sessions |
| Skills 统计 | Description token 分析 | 47 skills |

#### 2. 三面板布局

<!-- 面板截图待补充 -->
<!-- ![三面板布局](tests/screenshots/panels.png) -->

| 面板 | 功能 | 数据来源 |
|------|------|---------|
| **Sessions** | Token 使用进度条 | `tui_data.get_summary()` |
| **Files** | 废弃文件统计 | `get_hidden_folders()`, `get_large_files()` |
| **Skills** | Description token 分析 | 技能目录扫描 |

#### 3. 快捷操作

- 一键触发常用命令（archive/slim/cleanup/health）
- 实时刷新（5 秒间隔）
- 状态消息实时反馈

---

## 安装指南

### 系统要求

| 项目 | 要求 |
|------|------|
| Python | >= 3.8 |
| 终端 | 支持 UTF-8 和真彩色 |
| 操作系统 | Linux（首选）、macOS、Windows |

### 依赖安装

```bash
# 安装核心依赖
pip install textual>=8.0.0 rich>=13.0.0

# 当前版本
# textual: 8.2.1
# rich: 14.3.3
```

**项目 requirements.txt**：
```txt
textual>=8.0.0
rich>=13.0.0
```

### 验证安装

```bash
# 检查 Python 版本
python3 --version  # 需要 >= 3.8

# 测试 Textual 环境
python3 -c "from textual.app import App; print('OK')"

# 验证 Rich
python3 -c "from rich.console import Console; Console().print('[green]OK[/green]')"
```

---

## 快速开始

### 启动 TUI

```bash
# 进入项目目录
cd ~/.openclaw/workspace/skills/lobster-doctor

# 启动 TUI
python3 scripts/lobster_tui.py

# 或使用别名（如果已配置）
lobster-tui
```

### 界面布局（实际尺寸）

```
┌─────────────────────────────────────────────────────────────────┐
│ 🦞 Lobster Doctor  │  🟢 Healthy  │  16.7MB  │  📁 5  │ 🕐 22:51 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌── Sessions ─────────┐  ┌── Files ────────┐  ┌── Skills ─────┐│
│  │ 📊 Sessions         │  │ 📁 Files        │  │ 🎯 Skills     ││
│  │                     │  │                 │  │               ││
│  │ Total Sessions: 3   │  │ Hidden: 5 🟢    │  │ Total: 47     ││
│  │ Active: 2           │  │ Large: 0 🟢     │  │ Tokens: 150K  ││
│  │                     │  │ Violations: 0   │  │ Avg: 3,191    ││
│  │ Token Usage:        │  │                 │  │               ││
│  │ 250K / 1M (25.0%)   │  │ Total Waste: 0B │  │ Largest:      ││
│  │ [██████░░░░░░░] 🟢  │  │                 │  │ deep-research ││
│  └─────────────────────┘  └─────────────────┘  └───────────────┘│
│                                                                 │
│  Status: 系统就绪，按 H 进行健康检查                              │
├─────────────────────────────────────────────────────────────────┤
│ [A]rchive [S]lim [C]leanup [H]ealth [R]efresh [Q]uit            │
└─────────────────────────────────────────────────────────────────┘
```

### 首次使用流程

1. 启动 TUI（`python3 scripts/lobster_tui.py`）
2. 查看当前健康状况（Header 显示健康状态）
3. 按 **H** 运行健康检查
4. 根据状态消息执行相应操作
5. 按 **Q** 安全退出

<!-- GIF 演示待补充 -->
<!-- ![启动演示](tests/screenshots/demo.gif) -->

---

## 快捷键参考

### 全局快捷键速查表

| 快捷键 | 功能 | 说明 | 触发命令 |
|--------|------|------|---------|
| `A` | Archive | 归档旧记忆，延长会话续航 | `lobster_doctor.py archive` |
| `S` | Slim | 精简技能 description | `lobster_doctor.py slim` |
| `C` | Cleanup | 安全清理废弃文件 | `lobster_doctor.py cleanup` |
| `H` | Health | 运行全面健康检查 | `lobster_doctor.py health` |
| `R` | Refresh | 手动刷新当前状态 | 各面板 `_refresh_data()` |
| `Q` | Quit | 安全退出 TUI | `app.exit()` |

### 快捷键记忆口诀

> **A**rchive — 归档  
> **S**lim — 瘦身  
> **C**leanup — 清理  
> **H**ealth — 健康  
> **R**efresh — 刷新  
> **Q**uit — 退出

### 面板导航（暂未实现）

| 快捷键 | 功能 | 状态 |
|--------|------|------|
| `Tab` | 切换面板 | Phase 2 |
| `↑`/`↓` | 面板内滚动 | Phase 2 |
| `Enter` | 展开详情 | Phase 3 |

---

## 配置说明

### 配置参数（代码内定义）

| 配置项 | 默认值 | 位置 | 说明 |
|--------|--------|------|------|
| `REFRESH_INTERVAL` | 5 秒 | `tui_header.py`, `tui_panels.py` | 自动刷新间隔 |
| `HEALTH_THRESHOLDS.ok` | 500MB | `tui_data.py` | 健康阈值（绿色） |
| `HEALTH_THRESHOLDS.warn` | 1GB | `tui_data.py` | 警告阈值（黄色） |
| `PROTECTED_DIRS` | skills, node_modules, .git... | `tui_data.py` | 排除目录 |
| `CORE_FILES` | MEMORY.md, SOUL.md... | `tui_data.py` | 核心文件白名单 |

### 健康状态阈值

```python
# tui_data.py 定义
HEALTH_THRESHOLDS = {
    "ok": 500 * 1024 * 1024,      # 500MB → 🟢
    "warn": 1024 * 1024 * 1024,   # 1GB → 🟡/🔴
}
```

| 状态 | 图标 | Workspace 大小 | 说明 |
|------|------|----------------|------|
| 健康 | 🟢 | < 500MB | 状态良好，无需处理 |
| 注意 | 🟡 | 500MB - 1GB | 建议清理 |
| 危险 | 🔴 | > 1GB | 立即处理 |

### Token 占用阈值

| 状态 | 占比 | 颜色 | 说明 |
|------|------|------|------|
| 🟢 健康 | <50% | green | 大量空间 |
| 🟡 注意 | 50-70% | yellow | 开始关注 |
| ⚠️ 警告 | 70-85% | yellow | 建议处理 |
| 🔴 危险 | >85% | red | 立即处理 |

---

## 故障排查

### 常见问题

#### 1. TUI 无法启动

**症状**：运行 `python3 scripts/lobster_tui.py` 报错

**诊断步骤**：

```bash
# 1. 检查 Python 版本
python3 --version  # 需要 >= 3.8

# 2. 检查依赖安装
pip show textual
pip show rich

# 3. 检查导入路径
cd skills/lobster-doctor/scripts
python3 -c "from lobster_tui import LobsterDoctorApp; print('OK')"
```

**解决方案**：

```bash
# 安装缺失依赖
pip install textual>=8.0.0 rich>=13.0.0

# 如果 pip 不可用，使用 pip3
pip3 install textual rich

# 验证安装
python3 -c "import textual; import rich; print('Dependencies OK')"
```

#### 2. 界面显示异常（乱码/颜色错误）

**症状**：界面显示方块、颜色不正确

**诊断步骤**：

```bash
# 检查终端 Unicode 支持
echo "🦞 🟢 🟡 🔴"
# 如果显示方块，终端字体不支持 Unicode

# 检查终端颜色支持
echo -e "\033[31mRed\033[0m \033[32mGreen\033[0m \033[33mYellow\033[0m"
```

**解决方案**：

1. **更换终端字体**：使用支持 Unicode 的字体（如 JetBrains Mono、Fira Code）
2. **切换终端**：推荐使用 iTerm2 (macOS)、Windows Terminal (Windows)、Alacritty (Linux)
3. **检查 TERM 变量**：`echo $TERM`，应为 `xterm-256color` 或类似

#### 3. 刷新卡顿

**症状**：界面刷新慢，操作延迟

**诊断步骤**：

```bash
# 检查 workspace 大小
du -sh ~/.openclaw/workspace

# 检查文件数量
find ~/.openclaw/workspace -type f | wc -l
```

**解决方案**：

```bash
# 如果 workspace 过大，执行清理
python3 scripts/lobster_doctor.py cleanup

# 或在 TUI 中按 C 触发清理
```

#### 4. 快捷键无响应

**症状**：按快捷键没有反应，状态消息不更新

**可能原因**：
- 终端焦点不在 TUI 窗口
- 终端不支持按键捕获

**解决方案**：

```bash
# 测试终端按键支持
textual keys

# 如果按键无响应，尝试其他终端
```

#### 5. ModuleNotFoundError

**症状**：`ModuleNotFoundError: No module named 'tui_header'`

**解决方案**：

```bash
# 确保在正确目录运行
cd ~/.openclaw/workspace/skills/lobster-doctor/scripts

# 或添加路径
python3 scripts/lobster_tui.py
```

### 调试模式

```bash
# 启用 Textual 调试模式
textual console

# 查看 TUI 日志
TEXTUAL_DEBUG=1 python3 scripts/lobster_tui.py
```

### 性能监控

```bash
# 检查内存占用
python3 -c "
import tracemalloc
tracemalloc.start()
# 启动 TUI 代码...
current, peak = tracemalloc.get_traced_memory()
print(f'Peak: {peak / 1024 / 1024:.1f}MB')
"
```

---

## 文件结构

```
skills/lobster-doctor/
├── scripts/
│   ├── lobster_tui.py      # TUI 主程序
│   ├── tui_header.py       # Header 组件
│   ├── tui_panels.py       # 三面板组件
│   └── tui_data.py         # 数据层
├── tests/
│   ├── test_tui_components.py  # 组件测试
│   ├── test_tui_data.py        # 数据层测试
│   └── screenshots/            # 截图目录（待创建）
├── docs/
│   ├── tui-user-guide.md       # 本文档
│   └── tui-changelog.md        # 更新日志
└── requirements.txt        # 依赖列表
```

---

## 依赖清单

| 包 | 版本要求 | 当前版本 | 用途 |
|-----|---------|---------|------|
| textual | >=8.0.0 | 8.2.1 | TUI 框架 |
| rich | >=13.0.0 | 14.3.3 | 富文本渲染 |

**注意**：cachetools 在 Phase 2 中用于缓存，当前 MVP 不需要。

---

## 附录

### 命令行替代方案

如果 TUI 不可用，可使用命令行：

```bash
# 健康检查
python3 scripts/lobster_doctor.py health

# 查看摘要（JSON）
python3 scripts/lobster_doctor.py health --json

# 数据层测试
python3 -c "
import sys
sys.path.insert(0, 'scripts')
from tui_data import get_summary
import json
print(json.dumps(get_summary(), indent=2))
"
```

### 相关文档

- [README.md](../README.md) — 项目概述
- [KNOWLEDGE.md](../KNOWLEDGE.md) — 命令详细说明
- [tui-changelog.md](tui-changelog.md) — TUI 更新日志

---

_文档版本：v1.0 | 更新时间：2026-04-02 | 代码状态：MVP 完成，截图/GIF 待补充_