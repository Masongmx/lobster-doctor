---
name: lobster-doctor
description: OpenClaw workspace 健康管家。当用户提到清理、瘦身、归档、token用量、会话健康时触发。支持 health/archive/slim/cleanup 命令。每周定期执行健康检查。
---

# 🦞 龙虾医生

> 装得下，用得久，清得掉。

OpenClaw 的 workspace 健康管家。帮你监控会话健康、检测孤立进程、归档旧记忆，让 agent 跑得更久、更稳。

## 核心价值

| 价值 | 功能 | 说明 |
|------|------|------|
| **装得下** | Memory 归档 | 归档旧记忆，控制 memory 增长 |
| **用得久** | 会话监控 | 相对阈值告警，避免上下文溢出 |
| **清得掉** | 安全清理 | 白名单 + 备份 + 撤销，绝不误删 |

## 功能列表

| 功能 | 命令 | 触发方式 |
|------|------|----------|
| **健康检查** | `health` | Agent 主动（每周定期） |
| **Memory 归档** | `archive` | 用户触发："归档旧记忆" |
| **会话检查** | `session` | 用户触发："token 用量怎么样" |
| **技能瘦身** | `slim` | 用户触发："技能瘦身" |
| **安全清理** | `cleanup` | 用户触发："帮我清理一下" |

## Agent 主动触发规则

| 时机 | 执行动作 |
|------|----------|
| 每周定期 | 健康检查 → 发现问题推送到飞书 |

## 相对阈值设计

基于模型上下文窗口的百分比：

| 状态 | 阈值 | 说明 |
|------|------|------|
| 🟢 健康 | <50% | 大量空间 |
| 🟡 注意 | 50-70% | 开始关注 |
| ⚠️ 警告 | 70-85% | 建议处理 |
| 🔴 危险 | >85% | 立即处理 |

## 命令行用法

```bash
# 健康检查
python3 scripts/lobster_doctor.py health

# Memory 归档
python3 scripts/lobster_doctor.py archive

# 会话检查
python3 scripts/lobster_doctor.py session

# 技能瘦身
python3 scripts/lobster_doctor.py slim

# 安全清理
python3 scripts/lobster_doctor.py cleanup

# 撤销清理
python3 scripts/lobster_doctor.py cleanup --undo
```

## 安全机制

- **白名单保护**：核心文件永不删除
- **自动备份**：清理前自动备份
- **一键撤销**：支持 undo 操作
- **相对阈值**：适配不同模型
- **零 Token**：纯本地运行

## 安装

```bash
clawhub install lobster-doctor
```

## License

MIT
