---
name: lobster-doctor
description: >
  🦞 龙虾医生 — OpenClaw workspace 健康管家。会话监控+体检诊断+周报生成+安全清理+技能瘦身。说句话就能用。
  Activate when user mentions: 体检, 清理, workspace健康, 龙虾医生, lobster doctor,
  workspace cleanup, 垃圾文件, 废弃文件, 僵尸任务, cron巡检, token太贵, 技能太多,
  skill-slim, 技能瘦身, 清理一下, 做个体检, 整理workspace, 会话健康, 周报, session health.
---

# 🦞 龙虾医生 v2.1

你的 OpenClaw workspace 会越来越臃肿——会话历史堆积、临时文件堆积、技能描述膨胀、cron 任务遗忘。龙虾医生帮你自动治理。

**一句话**：「给龙虾做个体检」「会话健康怎么样」「生成周报」「清理一下」「技能太多了」——剩下的交给它。

---

## v2.0 新功能

### 🩺 会话健康监控
一句话：「会话健康怎么样」

自动检测所有会话的历史 token 大小：
- 超过 100K tokens → ⚠️ 警告
- 超过 200K tokens → 🚨 危险

**为什么重要**：会话历史占 98% 的 token 消耗，每次请求都在重复发送。

### 📊 周报生成
一句话：「生成周报」

每周日心跳触发，自动生成健康报告：
1. 会话健康统计（危险/警告会话）
2. 技能扫描结果
3. Workspace 清理建议

**推送逻辑**：
- 自动检测 `openclaw.json` 中已启用的渠道
- 飞书 chatId 从 `groupAllowFrom[0]` 自动获取
- 本地文件始终生成（兜底）

---

## 核心功能

### 🩺 体检诊断
一句话：「给龙虾做个体检」

自动扫描并报告：
- 废弃文件（超过3天未改的临时脚本）
- 重复文件（内容相同）
- 空目录、大文件
- 僵尸 cron 任务
- **0使用技能扫描**（检测从未触发的技能）
- **重复技能检测**（功能重叠的技能，如 tavily-search vs web-search）
- token 消耗估算

### 🧹 安全清理
一句话：「帮我清理一下」

**四重保障，绝不误删**：
- 核心文件白名单保护（MEMORY.md、SOUL.md 等）
- skills/、memory/、node_modules/ 绝不碰
- 清理前必须预览确认
- 自动备份，随时可恢复

### ✂️ 技能瘦身 ⭐ 独家
一句话：「技能太多了 / token 太贵」

**这是龙虾医生的杀手锏**——其他工具都没有。

**问题**：每个技能的 description 都注入系统提示。136 个技能 = 每轮 ~11K tokens 白白烧掉。

**解法**：精简 description，只保留核心功能句和触发关键词。description 是"门牌号"，不是"说明书"，精简不影响调用准确性。

**效果**：每轮节省 ~3,200 tokens，一天几十轮对话就是几万 tokens。

### 🔍 cron 巡检
一句话：「检查有没有僵尸任务」

发现已禁用、临时创建、长期未运行的任务。

---

## 使用方式

**直接说人话**，龙虾医生会自动理解并执行：

| 你说 | 它做 |
|------|------|
| 「会话健康怎么样」 | 检测会话历史 token 大小，输出健康报告 |
| 「生成周报」 | 生成周报并提示推送命令 |
| 「做个体检」 | 扫描并输出健康报告 |
| 「清理一下」 | 预览待清理文件 → 你确认 → 执行清理 |
| 「技能太多了」 | 分析技能描述体积 → 给出瘦身建议 |
| 「检查僵尸任务」 | 扫描 cron 任务列表 |

---

## 命令行

```bash
# 会话健康检查（v2.0 新增）
lobster_doctor.py session

# 周报生成（v2.0 新增）
lobster_doctor.py weekly

# 体检
lobster_doctor.py check

# 清理
lobster_doctor.py cleanup --dry-run  # 预览
lobster_doctor.py cleanup            # 执行

# 技能瘦身
lobster_doctor.py skill-slim report  # 查看报告
lobster_doctor.py skill-slim apply   # 应用精简

# Memory 归档
lobster_doctor.py memory-archive --apply
```

---

## 安全机制

- **预览优先**：任何修改操作都先展示预览
- **自动备份**：清理前自动备份到 `.cleanup-backup/`
- **白名单保护**：核心文件永远不会被删除
- **零 API 调用**：纯本地运行，不花钱

---

## 技术规格

- Python 3.8+，零外部依赖
- 纯本地运行，零 API 调用
- 支持 macOS / Linux / WSL

---

## 更新日志

### v2.1.0 (2026-03-24)
- ✨ 新增0使用技能扫描（检测从未触发的技能）
- ✨ 新增重复技能检测（功能重叠的技能）
- 🔧 支持搜索类、编码类、笔记类等多组重复技能检测

### v2.0 (2026-03-24)
- ✨ 新增会话健康监控命令 `session`
- ✨ 新增周报生成命令 `weekly`
- ✨ 自动检测已启用推送渠道（从 openclaw.json）
- ✨ 飞书 chatId 自动从 groupAllowFrom[0] 获取
- 🔧 优化 token 消耗诊断输出

### v1.3.0 (2026-03-24)
- 技能瘦身算法优化：滑动窗口去重
- 支持中英文精简
- 降低阈值支持短句