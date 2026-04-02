# KNOWLEDGE.md - Lobster Doctor 详细说明

## 目录

- [命令详解](#命令详解)
- [相对阈值计算](#相对阈值计算)
- [白名单文件](#白名单文件)
- [归档策略](#归档策略)
- [周报推送](#周报推送)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 命令详解

### health（健康检查）

全面诊断 workspace 状态，包括：
- Memory 文件数、总行数
- 会话健康状态
- 技能使用统计
- 孤立进程检测

```bash
python3 scripts/lobster_doctor.py health [--json]
```

**输出示例**：
```
🦞 龙虾医生 — 健康检查 (2026-03-26 18:15)

🔴 会话: 36 个, ~1.9M tokens (1452.5%)
   上下文窗口: 128K tokens
   剩余: ~-1731198 tokens
   🚨 危险会话: 4 个
   ⚠️  警告会话: 1 个

📦 废弃文件: 1 个, 20.6KB

🧩 技能: 102 个, description ~3K tokens

🧠 Bootstrap: ~101K tokens

⚠️ 发现 3 个问题:
   🔴 危险会话: 4 个
   🟡 警告会话: 1 个
   🧠 Bootstrap 过大: ~101K tokens
```

**参数**：
- `--json`：输出 JSON 格式，便于脚本解析

---

### session（会话检查）

基于相对阈值的 token 监控，显示各会话的健康状态。

```bash
python3 scripts/lobster_doctor.py session [--json]
```

**输出示例**：
```
📊 会话状态

🟢 session-001: 45% (57K/128K) - 健康
🟡 session-002: 62% (79K/128K) - 注意
⚠️  session-003: 78% (100K/128K) - 警告
🔴 session-004: 92% (118K/128K) - 危险

建议操作：
- session-004: 立即处理或归档
- session-003: 考虑清理或归档
```

---

### archive（Memory 归档）

归档过期 memory 文件，延长会话续航。

```bash
# 归档（默认 30 天前）
python3 scripts/lobster_doctor.py archive

# 自定义天数
python3 scripts/lobster_doctor.py archive --days 60

# 撤销归档
python3 scripts/lobster_doctor.py archive --undo
```

**归档规则**：
- 按日期创建 `memory/archive/YYYY-MM-DD-*.md`
- 合并碎片文件
- 保留 MEMORY.md 核心内容
- 保留带 📌 标记的永久记忆

**归档内容**：
- 超过指定天数的 memory 日志
- 已完成的任务记录
- 过期的待办事项

---

### slim（技能瘦身）

精简技能 description，减少 token 占用。

```bash
# 执行瘦身
python3 scripts/lobster_doctor.py slim

# 预览模式（不实际修改）
python3 scripts/lobster_doctor.py slim --dry-run
```

**瘦身策略**：
- 删除冗余注释
- 精简过长 SKILL.md
- 合理拆分 KNOWLEDGE.md

---

### cleanup（安全清理）

清理废弃文件，带白名单保护和自动备份。

```bash
# 执行清理
python3 scripts/lobster_doctor.py cleanup

# 撤销清理
python3 scripts/lobster_doctor.py cleanup --undo
```

**清理内容**：
- 临时文件（`*.tmp`, `*.bak`）
- 过期的 tar.gz 归档
- 孤立的 reference 文件
- 未使用的 node_modules

**安全机制**：
- 白名单文件永不删除
- 清理前自动备份到 `~/.openclaw/workspace/.cleanup-backup/`
- 支持 `--undo` 撤销

---

### system-health（系统体检）✨ 新增

检测整体系统健康状态。

```bash
python3 scripts/lobster_doctor.py system-health [--json]
```

**检测项**：
- workspace 大小
- `~/.openclaw/` 总大小
- 隐藏文件夹数量
- 大文件检测（>50MB）
- 违规结构检测（多工作区、重复配置、AI 工具残留）

**输出示例**：
```
🦞 OpenClaw 系统体检报告
==========================================

📊 大小统计:
   workspace: 358MB
   ~/.openclaw/: 462MB

📁 隐藏文件夹：10 个
   • .agents
   • .baoyu-skills
   ...

📦 大文件 (>50MB): 0 个

🔴 违规项：0 个

==========================================
整体状态：🟢 健康
```

---

### system-cleanup（系统清理）✨ 新增

整合清理流程，一站式系统维护。

```bash
python3 scripts/lobster_doctor.py system-cleanup [--json]
```

**清理流程**：

| 阶段 | 操作 | 说明 |
|------|------|------|
| Phase 1 | 安全清理 | 清理临时 tar.gz、reference、node_modules |
| Phase 2 | 结构修复 | 迁移 archive、删除重复配置 |
| Phase 3 | 深度清理 | 清理 AI 工具残留、.cleanup-backup |

**安全机制**：
- 自动备份到 `~/.openclaw/workspace/.cleanup-backup/`
- 详细日志输出
- 可撤销（从备份恢复）

---

## 相对阈值计算

基于模型上下文窗口的百分比，而非固定值：

```python
def get_status(usage_percent):
    if usage_percent < 50: return "🟢 健康"
    if usage_percent < 70: return "🟡 注意"
    if usage_percent < 85: return "⚠️ 警告"
    return "🔴 危险"
```

**优势**：
- 自动适配不同模型（GPT-4o 128K、Claude 200K 等）
- 避免固定阈值在不同模型间的不适配
- 提供相对准确的告警

---

## 白名单文件

以下核心文件永不删除：

```
MEMORY.md
SOUL.md
IDENTITY.md
USER.md
AGENTS.md
PROGRESS.md
rules/common/*.md
```

---

## 归档策略

### 自动归档

每周定期执行时，自动归档超过 30 天的记忆。

### 手动归档

用户可指定归档天数：

```bash
python3 scripts/lobster_doctor.py archive --days 60
```

### 保留策略

- 带 📌 标记的记忆永久保留
- MEMORY.md 核心内容不归档
- 归档文件保存在 `memory/archive/` 目录

---

## 周报推送

定期健康检查结果通过飞书推送。

**飞书格式标记**：`[FEISHU_REPORT]`

推送内容包括：
- 会话健康统计
- 发现的问题列表
- 建议操作

---

## 配置说明

### package.json 配置

```json
{
  "name": "lobster-doctor",
  "version": "v4.0.0",
  "config": {
    "defaultModel": "local",
    "requiresNet": false,
    "autoRun": {
      "command": "health",
      "schedule": "0 8 * * *"
    }
  }
}
```

**配置项说明**：

| 配置项 | 说明 |
|--------|------|
| `defaultModel` | 默认使用本地模型（不调用 LLM） |
| `requiresNet` | 不需要网络 |
| `autoRun.command` | 定期执行的命令 |
| `autoRun.schedule` | Cron 表达式（每周一 8:00） |

---

## 常见问题

### Q: 清理后如何恢复？

```bash
python3 scripts/lobster_doctor.py cleanup --undo
```

备份保存在 `~/.openclaw/workspace/.cleanup-backup/`。

### Q: 为什么使用相对阈值？

不同模型的上下文窗口差异很大（GPT-4o 128K vs Claude 200K）。固定阈值（如 50K tokens）在不同模型间不适配。相对阈值基于模型上下文窗口百分比，自动适配。

### Q: 归档会影响哪些文件？

- 超过指定天数的 `memory/YYYY-MM-DD.md` 文件
- 不影响 `MEMORY.md` 核心记忆
- 带 📌 标记的记忆保留

### Q: 白名单文件有哪些？

核心配置文件：`MEMORY.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `AGENTS.md`, `PROGRESS.md`, `rules/common/*.md`

### Q: Gotchas 汇总

| 问题 | 解决方案 |
|------|----------|
| 白名单不全误删 | ✅ 清理前检查 + --undo |
| 飞书格式错误 | ✅ [FEISHU_REPORT] 标记 |
| 线性阈值不适配 | ✅ 改用相对阈值 |
| 去重算法失败 | ✅ 调低阈值 10→6 |

---

_详细命令说明。SKILL.md 只保留核心功能列表。_