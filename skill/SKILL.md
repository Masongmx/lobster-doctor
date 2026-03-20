---
name: lobster-doctor
description: >
  🦞 龙虾医生 — OpenClaw workspace 健康管理。体检+清理+技能瘦身+cron巡检。
  Activate when user mentions: 体检, 清理, workspace健康, 龙虾医生, lobster doctor,
  workspace cleanup, 垃圾文件, 废弃文件, 僵尸任务, cron巡检, token太贵, 技能太多,
  skill-slim, 技能瘦身, 清理一下, 做个体检, 整理workspace。
---

# 🦞 Lobster Doctor

OpenClaw workspace 全生命周期健康管理：体检诊断 → 垃圾清理 → 技能瘦身 → 定期巡检。

## 自动行为（无需用户操作）

龙虾根据用户意图自动调用。用户只需**自然语言描述需求**。

### 体检
```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py check
```

### 清理（必须先 dry-run 再确认）
```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py cleanup --dry-run  # 预览
python3 skills/lobster-doctor/scripts/lobster_doctor.py cleanup           # 执行
```

### cron 巡检
```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py cron-audit
```

### 文件统计
```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py stats
```

### 技能瘦身
```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py skill-slim report    # 报告
python3 skills/lobster-doctor/scripts/lobster_doctor.py skill-slim dry-run   # 预览
python3 skills/lobster-doctor/scripts/lobster_doctor.py skill-slim apply     # 执行
```

### 设置每周自动体检
```bash
openclaw cron add --name "lobster-doctor-weekly" --cron "0 9 * * 1" \
  --payload '{"kind":"systemEvent","text":"运行龙虾医生体检：执行 lobster_doctor.py check，将结果通知用户。"}' \
  --session-target isolated
```

## 用户意图识别

| 用户可能说的话 | 龙虾执行 |
|--------------|---------|
| "给我的龙虾做个体检" | `check` |
| "检查一下 workspace 健康" | `check` |
| "帮我清理一下 workspace" | 先 `cleanup --dry-run`，确认后 `cleanup` |
| "检查有没有僵尸任务" | `cron-audit` |
| "看看文件分布" | `stats` |
| "技能太多了/token太贵" | `skill-slim report` |
| "精简技能描述" | `skill-slim dry-run` → 确认 → `skill-slim apply` |
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
安全自动清理。四重保障：
- ✅ 核心文件白名单（SOUL.md, MEMORY.md 等）
- ✅ skills/ node_modules/ memory/ 不碰
- ✅ 自动备份到 `.cleanup-backup/YYYY-MM-DD/`
- ✅ `--dry-run` 模拟清理

**⚠️ cleanup 前必须先 --dry-run 让用户确认！**

### cron-audit（cron 巡检）
检测僵尸 cron 任务：已禁用、临时任务、长期未运行。

### stats（统计）
workspace 文件分布：按类型、按目录大小、已安装技能数量。

### skill-slim（技能瘦身）⭐ 新功能
**问题**：每个技能的 description 都注入系统提示，136个技能 = 每轮 ~11K tokens 白烧。

**原理**：OpenClaw 加载流程是 `description 判断 → read SKILL.md → 执行`，description 只是"门牌号"不是"说明书"。精简 description 不影响调用准确性。

**精简策略**：
1. 保留核心功能句（一句话说清干什么）
2. 保留触发关键词（Activate when / Triggers）
3. 保留排除条件（NOT for，限制100字符内）
4. 删除冗长解释、Use when 列表、示例
5. 每条硬上限 150 字符
6. 龙虾医生自身不精简（白名单保护）

**安全机制**：
- `report` / `dry-run` 不修改任何文件
- `apply` 自动备份原 SKILL.md 到 `.cleanup-backup/skill-slim/`
- 随时可从备份恢复

**实测效果**（2026-03-20）：
| 指标 | 原始 | 精简后 |
|------|------|--------|
| Description 总字符 | 22,387 | 9,919 |
| 纯 description tokens | ~5,596 | ~2,479 |
| 含 XML 标签 tokens | ~10,312 | ~7,195 |
| **每轮节省** | — | **~3,200 tokens** |

## 依赖

- Python 3.8+（零外部包）
- 零 API 调用
