# 🦞 龙虾医生

> **装得下，用得久，清得掉。**

OpenClaw 的 workspace 健康管家。帮你监控会话健康、检测孤立进程、归档旧记忆，让 agent 跑得更久、更稳。

## 快速开始

```bash
# 健康检查（你说："检查一下健康"）
python3 scripts/lobster_doctor.py health

# Memory 归档（你说："归档旧记忆"）
python3 scripts/lobster_doctor.py archive

# 会话检查（你说："token 用量怎么样"）
python3 scripts/lobster_doctor.py session
```

## 功能

| 功能 | 命令 | 说明 |
|------|------|------|
| **健康检查** | `health` | **P0**：全面诊断 workspace 状态 |
| **Memory 归档** | `archive` | **P0**：归档旧记忆，延长会话续航 |
| **会话检查** | `session` | **P1**：基于相对阈值的 token 监控 |
| **技能瘦身** | `slim` | **P2**：精简 description，锦上添花 |
| **安全清理** | `cleanup` | **P1**：清理废弃文件，白名单保护 |

## 核心价值

| 价值 | 功能 | 说明 |
|------|------|------|
| **装得下** | Memory 归档 | 归档旧记忆，控制 memory 增长 |
| **用得久** | 会话监控 | 相对阈值告警，避免上下文溢出 |
| **清得掉** | 安全清理 | 白名单 + 备份 + 撤销，绝不误删 |

## 用户怎么说，Agent 怎么做

| 用户说的话 | Agent 的动作 |
|------------|-------------|
| "检查一下健康" | 执行全面健康检查 |
| "归档旧记忆" | 归档过期 memory 文件 |
| "token 用量怎么样" | 检查会话 token 使用率 |
| "技能瘦身" | 精简技能 description |
| "帮我清理一下" | 安全清理废弃文件 |

**Agent 主动触发**：
- 每周定期：健康检查，发现问题推送到飞书

## 健康检查输出

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

## 相对阈值设计

基于模型上下文窗口的百分比，而非固定值：

| 状态 | 阈值 | 说明 |
|------|------|------|
| 🟢 健康 | <50% | 大量空间 |
| 🟡 注意 | 50-70% | 开始关注 |
| ⚠️ 警告 | 70-85% | 建议处理 |
| 🔴 危险 | >85% | 立即处理 |

**优势**：适配不同模型（GPT-4o 128K、Claude 200K 等），阈值自动调整。

## Memory 归档

归档过期 memory 文件，延长会话续航：

```bash
# 归档（默认 30 天前）
python3 scripts/lobster_doctor.py archive

# 自定义天数
python3 scripts/lobster_doctor.py archive --days 60

# 撤销归档
python3 scripts/lobster_doctor.py archive --undo
```

**归档内容**：
- 超过指定天数的 memory 日志
- 已完成的任务记录
- 过期的待办事项

**安全机制**：
- 归档前备份
- 保留永久标记（📌）的记忆
- 支持撤销

## 安全机制

- **白名单保护**：核心文件永不删除
- **自动备份**：清理前自动备份到 `.cleanup-backup/`
- **一键撤销**：`cleanup --undo` / `archive --undo`
- **相对阈值**：适配不同模型的上下文窗口
- **零 Token**：纯本地运行，不调用 LLM

## 安装

```bash
clawhub install lobster-doctor
```

## 更新日志

- v4.0.0: 重新定位"装得下，用得久，清得掉"，新增 Memory 归档、相对阈值、孤立进程检测
- v3.0.0: 精简到 4 个核心命令，Agent 主动健康检查
- v2.2.0: Token 监控告警、飞书推送修复
- v2.0.0: 会话健康监控、周报生成

## License

MIT
