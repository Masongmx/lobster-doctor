---
name: lobster-doctor
description: |
  🦞 龙虾医生 — workspace 健康管理。体检+清理+cron巡检，解决 OpenClaw 长期使用后的文件膨胀问题。
---

# 🦞 Lobster Doctor

诊断 + 治疗 + 预防：让你的龙虾保持健康。

## 问题

OpenClaw 用久了会越来越臃肿：
- 废弃的测试脚本堆积在根目录
- 方案废弃但目录还在
- cron 僵尸任务偷偷在跑
- 重复文件浪费空间
- workspace 越来越大 → bootstrap context 越来越多 → token 越来越贵

## 功能

| 命令 | 功能 | 建议频率 |
|------|------|---------|
| `check` | 体检：扫描 workspace，输出健康报告 | 每周 |
| `cleanup` | 治疗：安全自动清理（清理前自动备份） | 每月 |
| `cron-audit` | 巡检：检测 cron 僵尸任务 | 每月 |
| `stats` | 统计：workspace 文件分布概览 | 按需 |

## 体检报告内容

- 根目录非核心文件数量
- 废弃文件检测（超过3天未修改的 .py/.js/.html）
- 重复文件检测（内容 hash 相同）
- 空目录检测
- 大文件检测（>1MB）
- cron 僵尸任务检测
- bootstrap context token 估算
- 记忆树状态（如已安装）

## 安全保障

- ✅ 核心文件白名单永不删除（SOUL.md, MEMORY.md 等）
- ✅ skills/ node_modules/ memory/ memory-tree/ 不碰
- ✅ 清理前自动备份到 `.cleanup-backup/YYYY-MM-DD/`
- ✅ 支持 `--dry-run` 模拟清理（只报告不删除）

## 使用

```bash
# 体检
python3 skills/lobster-doctor/scripts/lobster_doctor.py check

# 模拟清理（先看看会删什么）
python3 skills/lobster-doctor/scripts/lobster_doctor.py cleanup --dry-run

# 实际清理
python3 skills/lobster-doctor/scripts/lobster_doctor.py cleanup

# cron 巡检
python3 skills/lobster-doctor/scripts/lobster_doctor.py cron-audit

# 文件统计
python3 skills/lobster-doctor/scripts/lobster_doctor.py stats
```

## 定时巡检

```bash
# 每周日凌晨5点自动体检
openclaw cron add --name "lobster-doctor-check" --cron "0 5 * * 0" \
  --system-event "RUN:python3 ~/.openclaw/workspace/skills/lobster-doctor/scripts/lobster_doctor.py check" \
  --session main
```

## 依赖

- Python 3.8+（不需要 pip 安装任何包）
- 零 API 调用
