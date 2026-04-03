---
name: lobster-doctor
description: OpenClaw workspace 健康管家。当用户提到清理、瘦身、归档、token 用量、会话健康、系统体检、可视化、TUI 时触发。支持 health/archive/slim/cleanup/system-health/system-cleanup 命令 + TUI 可视化界面。每周定期执行健康检查。
---

# 🦞 龙虾医生

[![OpenClaw](https://img.shields.io/badge/OpenClaw-%3E%3D0.3.0-blue)](https://github.com/Masongmx/openclaw)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **装得下，用得久，清得掉。**

OpenClaw 的 workspace 健康管家。监控会话健康、检测孤立进程、归档旧记忆，让 agent 跑得更久更稳。

## 核心命令

| 命令 | 优先级 | 用途 |
|------|--------|------|
| `health` | **P0** | 全面诊断 workspace 状态 |
| `archive` | **P0** | 归档旧记忆，延长会话续航 |
| `session` | **P1** | 基于相对阈值的 token 监控 |
| `cleanup` | **P1** | 安全清理废弃文件 |
| `slim` | **P2** | 精简技能 description |
| `system-health` | **P1** | 系统体检（文件夹结构 + 大小分析） |
| `system-cleanup` | **P1** | 整合清理流程 |
| `TUI` | **P1** | 可视化终端界面（交互式） |

## 快速开始

```bash
# 健康检查
python3 scripts/lobster_doctor.py health

# 归档旧记忆（默认 30 天）
python3 scripts/lobster_doctor.py archive

# 检查 token 用量
python3 scripts/lobster_doctor.py session

# 安全清理
python3 scripts/lobster_doctor.py cleanup --undo  # 撤销

# 🖥️ 可视化界面（TUI）
python3 scripts/lobster_tui.py
```

## 相对阈值设计

基于模型上下文窗口的百分比：

| 状态 | 占比 | 说明 |
|------|------|------|
| 🟢 健康 | <50% | 大量空间 |
| 🟡 注意 | 50-70% | 开始关注 |
| ⚠️ 警告 | 70-85% | 建议处理 |
| 🔴 危险 | >85% | 立即处理 |

**优势**：自动适配 GPT-4o (128K)、Claude (200K) 等不同模型。

## 安全机制

| 机制 | 说明 |
|------|------|
| 白名单保护 | 核心文件永不删除 |
| 自动备份 | 清理前备份到 `.cleanup-backup/` |
| 一键撤销 | `--undo` 恢复 |
| 零 Token | 纯本地运行，不调用 LLM |

## 用户怎么说，Agent 怎么做

| 用户说的话 | Agent 的动作 |
|------------|-------------|
| "检查一下健康" | 执行全面健康检查 |
| "归档旧记忆" | 归档过期 memory 文件 |
| "token 用量怎么样" | 检查会话 token 使用率 |
| "技能瘦身" | 精简技能 description |
| "帮我清理一下" | 安全清理废弃文件 |
| "系统体检" | 运行系统健康诊断 |
| "打开可视化界面" / "TUI" | 提示用户去终端运行 lobster_tui.py |

**注意**：TUI 是交互式终端界面，需要在本地终端运行，无法通过消息渠道直接操作。Agent 会告诉用户具体命令。

**Agent 主动触发**：每周定期执行健康检查，发现问题推送到飞书。

## 安装

```bash
clawhub install lobster-doctor
```

---

详细命令说明见 [KNOWLEDGE.md](KNOWLEDGE.md) | 英文文档见 [README.md](README.md)