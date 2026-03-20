---
name: lobster-doctor
version: 1.1.0
description: |
  🦞 龙虾医生 — OpenClaw workspace 全生命周期健康管理。体检+清理+技能瘦身+cron巡检。零依赖、零API调用。
tags: [maintenance, cleanup, workspace, health, automation, optimization, token-saving]
---

# 🦞 Lobster Doctor — 龙虾医生

> **你的龙虾用久了越来越慢？workspace 塞满了废弃文件？技能装了136个 description 占了 11000 tokens？token 越花越多？**
>
> 龙虾医生 v1.1：体检、清理、**技能瘦身**、cron 巡检，让你的龙虾保持健康和精简。

## 💡 为什么需要这个？

OpenClaw 用了几周之后，你的 workspace 大概长这样：

```
workspace/
├── test_model_switch.md          # 调试完再也没打开
├── fibonacci_analysis.py          # 测试完的脚本
├── model-switcher-enhanced.html   # 试了两次就弃用
├── dispatch_research_task.js      # 废弃方案残留
├── openclaw_report_20260317.md    # 过期报告
├── backup/                        # 不知道什么时候建的
├── research-analyst/              # 方案废弃但目录还在
└── ...（40+个文件，真正有用的不到15个）
```

**这不是个别现象，是所有活跃用户的普遍痛点。**

- Facebook OpenClaw 社区有人发帖 "workspace became messy"
- GitHub 上有人提了 "Memory Guardian" 概念
- Reddit 大量讨论 memory bloat 和 context overflow

## 🎯 我们的差异化

| | 现有方案 | 🦞 龙虾医生 |
|--|--|--|
| workspace-organization (LobeHub) | ❌ 只出体检报告 | ✅ 诊断 + 自动清理 |
| Memory Tree (我们) | ❌ 只管记忆文件 | ✅ 文件层面 + cron + token |
| 手动 `rm -rf` | ❌ 不安全，容易误删 | ✅ 白名单保护 + 自动备份 |
| 什么都不做 | ❌ 越用越臃肿 | ✅ 定期巡检，防患于未然 |

**核心卖点：别人只做"诊断报告"，我们做"诊断 + 治疗 + 预防"一体化。**

## 🔧 四大功能

### 1️⃣ check — 体检

```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py check
```

扫描 workspace，输出完整健康报告：
- 📁 根目录文件数量（非核心文件警告）
- 🗑️ 废弃文件检测（超过3天未修改的脚本）
- 📋 重复文件检测（内容 hash 相同）
- 📂 空目录检测
- 📦 大文件检测（>1MB）
- ⏰ cron 僵尸任务检测
- 🧠 Bootstrap Context Token 估算
- 🌳 记忆树健康度（如已安装）

### 2️⃣ cleanup — 安全清理

```bash
# 先模拟，看看会删什么
python3 skills/lobster-doctor/scripts/lobster_doctor.py cleanup --dry-run

# 确认后实际清理
python3 skills/lobster-doctor/scripts/lobster_doctor.py cleanup
```

**安全保障：**
- ✅ 核心文件白名单永不删除
- ✅ skills/ node_modules/ memory/ 不碰
- ✅ 清理前自动备份到 `.cleanup-backup/YYYY-MM-DD/`
- ✅ 支持 `--dry-run` 模拟模式

### 3️⃣ skill-slim — 技能瘦身 ⭐ v1.1 新功能

```bash
# 查看token消耗报告
python3 skills/lobster-doctor/scripts/lobster_doctor.py skill-slim report

# 预览精简效果
python3 skills/lobster-doctor/scripts/lobster_doctor.py skill-slim dry-run

# 执行精简（自动备份）
python3 skills/lobster-doctor/scripts/lobster_doctor.py skill-slim apply
```

**问题：** 136个技能的description注入系统提示，每轮消耗 ~11,000 tokens。

**原理：** OpenClaw加载流程是 `description判断 → read SKILL.md → 执行`，description只是"门牌号"不需要说明书。

**精简策略：** 保留核心功能句 + 触发关键词 + 排除条件，删除冗余解释，硬限150字符。

**实测效果（136个技能）：**

| 指标 | 精简前 | 精简后 |
|------|--------|--------|
| Description总字符 | 22,387 | 9,919 |
| 每轮tokens | ~5,600 | ~2,500 |
| **节省** | — | **~3,100 tokens/轮** |

### 4️⃣ cron-audit — Cron 巡检

```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py cron-audit
```

检测：
- 已禁用的僵尸任务
- 名称含 test/debug/tmp 的临时任务
- 任务创建时间和下次运行时间

### 5️⃣ stats — 文件统计

```bash
python3 skills/lobster-doctor/scripts/lobster_doctor.py stats
```

- 按类型分布（.md/.py/.js 等）
- 按目录大小排行
- 已安装技能数量和大小
- 记忆日志统计

## ⚡ 零门槛安装

```bash
# 方法1：从 GitHub 克隆
git clone https://github.com/Masongmx/lobster-doctor.git
cp -r lobster-doctor/skill/* ~/.openclaw/workspace/skills/lobster-doctor/

# 方法2：下载 .skill 包（从 GitHub Releases）
openclaw skill install lobster-doctor.skill
```

**依赖：**
- Python 3.8+（不需要 pip 安装任何包）
- 零 API 调用
- 零额外配置

## 📅 建议的自动化设置

```bash
# 每周日凌晨5点自动体检（只报告，不清理）
openclaw cron add --name "lobster-weekly-check" --cron "0 5 * * 0" \
  --system-event "CHECK:workspace health" \
  --session main
```

> 注意：`cleanup` 命令建议手动执行或设为人工确认，避免误删。

## 🏥 真实案例

**清理前（养了6周的龙虾）：**
- 根目录 40+ 文件
- 15+ 子目录（大部分是废弃方案）
- 0 个非核心文件被标记
- 记忆树健康度 0%

**清理后：**
- 根目录 13 个文件（全部有效）
- 4 个子目录
- 0 个问题
- 释放空间 706MB（含备份）

## 📄 License

MIT

## 🙏 Credit

- 灵感来源：[workspace-organization](https://lobehub.com/skills/openclaw-skills-workspace-organization)（LobeHub）
- 生态伙伴：[Memory Tree](https://github.com/Masongmx/memory-tree)（记忆生命周期管理）
