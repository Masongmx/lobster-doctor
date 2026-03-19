---
name: lobster-doctor
description: >
  🦞 龙虾医生 — workspace 健康管理。体检+清理+cron巡检，解决 OpenClaw 长期使用后的文件膨胀问题。
  Activate when user mentions: 体检, 清理, 清理workspace, workspace健康, 龙虾医生,
  lobster doctor, workspace cleanup, 垃圾文件, 废弃文件, 僵尸任务, cron巡检,
  检查workspace, workspace太大了, token变贵了, 清理一下, 做个体检, 整理workspace。
---

# 🦞 Lobster Doctor

诊断 + 治疗 + 预防：让你的龙虾保持健康。

## 自动行为（无需用户操作）

龙虾会根据用户意图自动调用相应功能。用户只需要**用自然语言描述需求**，龙虾会自动判断并执行。

**当用户要求体检/检查时**，龙虾自动执行：
```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py check
```

**当用户要求清理时**，龙虾**必须先执行模拟清理**，把结果展示给用户确认，得到用户同意后再执行实际清理：
```bash
# 第一步：模拟清理（展示会删除什么）
python3 skills/lobster-doctor/scripts/lobster_doctor.py cleanup --dry-run

# 第二步：用户确认后，实际清理
python3 skills/lobster-doctor/scripts/lobster_doctor.py cleanup
```

**当用户要求检查 cron 任务时**：
```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py cron-audit
```

**当用户要求查看文件统计时**：
```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py stats
```

**当用户要求设置定期体检时**：
```bash
openclaw cron add --name "lobster-doctor-weekly" --cron "0 9 * * 1" --payload '{"kind":"systemEvent","text":"运行龙虾医生体检：执行 lobster_doctor.py check，将结果通知用户。"}' --session-target isolated
```

## 用户意图识别

| 用户可能说的话 | 龙虾应该执行 |
|--------------|-------------|
| "给我的龙虾做个体检" | `check` |
| "检查一下 workspace 健康" | `check` |
| "龙虾是不是变慢了" | `check` |
| "帮我清理一下 workspace" | 先 `cleanup --dry-run`，确认后 `cleanup` |
| "清理垃圾文件" | 先 `cleanup --dry-run`，确认后 `cleanup` |
| "整理一下 workspace" | 先 `cleanup --dry-run`，确认后 `cleanup` |
| "检查有没有僵尸任务" | `cron-audit` |
| "看看 workspace 文件分布" | `stats` |
| "设置每周自动体检" | 创建 cron 定时任务 |

## 功能说明

### check（体检）
扫描 workspace，输出健康报告：
- 根目录非核心文件数量
- 废弃文件检测（超过3天未修改的 .py/.js/.html）
- 重复文件检测（内容 hash 相同）
- 空目录检测
- 大文件检测（>1MB）
- cron 僵尸任务检测
- bootstrap context token 估算

### cleanup（清理）
安全自动清理垃圾文件。四重安全保障：
- ✅ 核心文件白名单永不删除（SOUL.md, MEMORY.md 等）
- ✅ skills/ node_modules/ memory/ memory-tree/ 不碰
- ✅ 清理前自动备份到 `.cleanup-backup/YYYY-MM-DD/`
- ✅ 支持 `--dry-run` 模拟清理

**⚠️ 重要：执行 cleanup 前必须先运行 --dry-run 让用户确认！**

### cron-audit（cron 巡检）
检测 cron 僵尸任务：
- 已禁用但仍存在的任务
- 名称含 test/debug/tmp 的临时任务
- 长期未运行的任务

### stats（统计）
workspace 文件分布概览：
- 按类型分布
- 按目录大小排行
- 已安装技能数量和大小

## 依赖

- Python 3.8+（不需要 pip 安装任何包）
- 零 API 调用
