# 🦞 Lobster Doctor

OpenClaw workspace 全生命周期健康管理。

## 功能

### check（体检）
扫描 workspace 健康状况：废弃文件、重复文件、空目录、大文件、cron 僵尸任务、token 估算。

### cleanup（清理）
安全清理垃圾文件，四重保障（白名单、保护目录、自动备份、dry-run）。

### cron-audit（cron 巡检）
检测僵尸 cron 任务。

### stats（统计）
workspace 文件分布概览。

### skill-slim（技能瘦身）⭐ v1.1 新功能
精简所有技能的 description，减少每轮对话的 token 消耗。实测节省 56%，每轮省 ~3,200 tokens。

**原理**：OpenClaw 加载流程是 `description → read SKILL.md → 执行`，description 只是门牌号，不需要说明书。

**精简策略**：保留核心功能句 + 触发关键词 + 排除条件，删除冗长解释，硬限 150 字符。

**安全机制**：report/dry-run 不修改，apply 自动备份，随时可恢复。

## 使用

```bash
# 体检
python3 scripts/lobster_doctor.py check

# 清理（先预览再执行）
python3 scripts/lobster_doctor.py cleanup --dry-run
python3 scripts/lobster_doctor.py cleanup

# 技能瘦身
python3 scripts/lobster_doctor.py skill-slim report
python3 scripts/lobster_doctor.py skill-slim dry-run
python3 scripts/lobster_doctor.py skill-slim apply
```

## 依赖

- Python 3.8+
- 零外部包
- 零 API 调用

## 适用

任何安装了较多技能的 OpenClaw 实例。技能越多，瘦身效果越明显。

## License

MIT
