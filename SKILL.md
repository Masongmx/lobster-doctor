---
name: lobster-doctor
description: OpenClaw workspace 健康管家。当用户提到清理、瘦身、归档、token 用量、会话健康、系统体检、优化、减重时触发。自动执行健康检查和清理操作，用自然语言交互，不要让用户敲命令。
---

# 🦞 龙虾医生

OpenClaw 的 workspace 健康管家。找出消耗 token、拖慢速度、占用内存的大户，一键清理，实现精简瘦身。

## 用户怎么说，Agent 怎么做

| 用户说 | Agent 动作 |
|--------|-----------|
| "帮我清理一下" / "一键清理" | 执行 `fix` 命令，自动归档 + 清理 |
| "检查一下健康" | 执行 `health` 命令，报告问题和影响 |
| "token 用量怎么样" | 执行 `session` 命令，检查会话状态 |
| "系统体检" | 执行 `system-health` 命令 |
| "归档旧记忆" | 执行 `archive` 命令 |
| "技能瘦身" | 执行 `slim` 命令 |

**Agent 执行流程**：
1. 用户说自然语言 → Agent 识别意图
2. Agent 调用脚本执行 → 获取结果
3. Agent 用自然语言汇报 → 不展示命令行

## 核心命令

| 命令 | 用途 |
|------|------|
| `fix` | 一键清理（归档 + 瘦身 + 清理） |
| `health` | 健康检查 |
| `session` | 会话 token 检查 |
| `archive` | 归档旧记忆 |
| `slim` | 技能瘦身 |
| `cleanup` | 安全清理 |
| `system-health` | 系统体检 |

## 脚本位置

```python
# Agent 调用方式（内部）
import subprocess
result = subprocess.run(['python3', 'skills/lobster-doctor/scripts/lobster_doctor.py', 'health'], capture_output=True, text=True)
print(result.stdout)
```

## 报告格式

**health 输出**：问题 + 影响 + 一键清理建议 + 预估效果

**fix 输出**：归档统计 + 清理统计 + 总体效果

## 定期执行

每周自动健康检查，发现问题推送到飞书。