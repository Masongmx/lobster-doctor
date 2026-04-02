# 龙虾医生 TUI 可视化 Phase 1 (MVP) 开发计划

> **目标**：2-3 天完成 MVP，交付可用的终端可视化界面
> **技术栈**：Textual + Rich
> **原则**：拆细任务、多轮评审、反复验证、有效验收

---

## 📋 任务拆解（粒度：4-8 小时/任务）

### Task 1: 环境准备与依赖安装 ⏱️ 2h
**负责人**：developer
**验收标准**：
- [ ] `pip install textual rich` 成功
- [ ] `textual console` 测试通过
- [ ] 创建 `scripts/lobster_tui.py` 骨架
- [ ] Hello World TUI 运行正常

**输出**：
- `scripts/lobster_tui.py` (基础骨架)
- `requirements.txt` (依赖列表)

---

### Task 2: 核心数据层开发 ⏱️ 4h
**负责人**：developer
**验收标准**：
- [ ] `get_workspace_size()` 函数
- [ ] `get_hidden_folders()` 函数
- [ ] `get_large_files()` 函数
- [ ] `get_violations()` 函数
- [ ] 单元测试通过（pytest）

**输出**：
- `scripts/tui_data.py` (数据层模块)
- `tests/test_tui_data.py` (单元测试)

---

### Task 3: Header 组件开发 ⏱️ 4h
**负责人**：developer
**验收标准**：
- [ ] 显示 workspace 大小（带颜色标记）
- [ ] 显示隐藏文件夹数量
- [ ] 显示健康状态图标（🟢🟡🔴）
- [ ] 自动刷新（5 秒间隔）

**输出**：
- `scripts/tui_header.py` (Header 组件)
- 截图验证（`tests/screenshots/header.png`）

---

### Task 4: 三面板布局开发 ⏱️ 6h
**负责人**：developer
**验收标准**：
- [ ] Sessions 面板（token 占用进度条）
- [ ] Files 面板（废弃文件统计）
- [ ] Skills 面板（description token 统计）
- [ ] 面板可滚动
- [ ] 颜色标记（🟢🟡🔴）

**输出**：
- `scripts/tui_panels.py` (面板组件)
- 截图验证（`tests/screenshots/panels.png`）

---

### Task 5: ActionBar 组件开发 ⏱️ 4h
**负责人**：developer
**验收标准**：
- [ ] 快捷键绑定（A/S/C/H/R/Q）
- [ ] 按键提示显示
- [ ] 按键响应测试
- [ ] 确认对话框（防止误操作）

**输出**：
- `scripts/tui_action_bar.py` (ActionBar 组件)
- 交互测试视频

---

### Task 6: 集成与联调 ⏱️ 6h
**负责人**：developer
**验收标准**：
- [ ] 所有组件集成到 `lobster_tui.py`
- [ ] 实时刷新正常（5 秒）
- [ ] 快捷键响应正常
- [ ] 无内存泄漏（运行 30 分钟测试）

**输出**：
- `scripts/lobster_tui.py` (完整版)
- 压力测试报告

---

### Task 7: 文档与示例 ⏱️ 3h
**负责人**：social-media-operator
**验收标准**：
- [ ] README.md 更新（TUI 章节）
- [ ] 使用示例（GIF 演示）
- [ ] 快捷键参考表
- [ ] 故障排查指南

**输出**：
- `docs/tui-user-guide.md`
- README.md 更新

---

### Task 8: 评审与修复 ⏱️ 4h
**负责人**：reviewer
**验收标准**：
- [ ] 代码评审报告（≥3 个问题）
- [ ] 所有问题修复
- [ ] 二次评审通过
- [ ] 性能测试通过

**输出**：
- `memory/reviews/2026-04-xx-tui-review.md`
- 修复记录

---

## 🔄 评审机制

### 评审轮次
| 轮次 | 时机 | 参与人 | 输出 |
|------|------|--------|------|
| R1 | Task 2 完成 | reviewer | 数据层评审报告 |
| R2 | Task 4 完成 | reviewer | UI 组件评审报告 |
| R3 | Task 6 完成 | reviewer + main | 集成评审报告 |
| R4 | Task 8 完成 | main | 最终验收报告 |

### 评审检查清单
```markdown
## 代码质量
- [ ] 函数长度 <50 行
- [ ] 单一职责原则
- [ ] 错误处理完整
- [ ] 日志记录充分

## 性能
- [ ] 启动时间 <2 秒
- [ ] 刷新间隔 5 秒
- [ ] 内存占用 <50MB
- [ ] 无内存泄漏

## 用户体验
- [ ] 颜色对比度足够
- [ ] 快捷键易记
- [ ] 错误提示清晰
- [ ] 帮助信息完整
```

---

## 📊 验收标准（MVP）

### 功能验收
| 功能 | 验收标准 | 状态 |
|------|----------|------|
| workspace 大小显示 | 实时更新，误差<1MB | ⬜ |
| 隐藏文件夹计数 | 准确，与`ls -d`一致 | ⬜ |
| 健康状态颜色 | 🟢<500MB, 🟡500MB-1GB, 🔴>1GB | ⬜ |
| 快捷键 A | 触发 archive 命令 | ⬜ |
| 快捷键 S | 触发 slim 命令 | ⬜ |
| 快捷键 C | 触发 cleanup 命令 | ⬜ |
| 快捷键 H | 触发 health 命令 | ⬜ |
| 快捷键 R | 手动刷新 | ⬜ |
| 快捷键 Q | 安全退出 | ⬜ |

### 性能验收
| 指标 | 目标 | 实测 | 状态 |
|------|------|------|------|
| 启动时间 | <2 秒 | - | ⬜ |
| 刷新间隔 | 5 秒 | - | ⬜ |
| 内存占用 | <50MB | - | ⬜ |
| CPU 占用 | <5% | - | ⬜ |

### 质量验收
| 指标 | 目标 | 实测 | 状态 |
|------|------|------|------|
| 代码覆盖率 | >70% | - | ⬜ |
| 评审问题数 | ≥3 个 | - | ⬜ |
| 修复率 | 100% | - | ⬜ |
| 压力测试 | 30 分钟无崩溃 | - | ⬜ |

---

## 🚀 执行流程

```
Task 1 (环境) → Task 2 (数据) → Task 3 (Header)
     ↓              ↓              ↓
  验证 1         评审 R1        验证 3
                                ↓
Task 6 (集成) ← Task 5 (Action) ← Task 4 (Panels)
     ↓              ↓              ↓
  评审 R3        验证 5        评审 R2
     ↓
Task 8 (评审修复) → Task 7 (文档)
     ↓              ↓
  评审 R4        验证 7
     ↓
  最终验收 ✅
```

---

## 📝 沟通机制

### 每日站会（22:00）
- 今天完成了什么
- 明天计划做什么
- 有什么阻碍

### 即时汇报
- 任务完成 → 立即汇报
- 遇到问题 → 立即求助
- 评审完成 → 立即通知

### 交付物管理
- 代码：`skills/lobster-doctor/scripts/`
- 测试：`skills/lobster-doctor/tests/`
- 文档：`skills/lobster-doctor/docs/`
- 评审：`memory/reviews/`

---

## ⚠️ 风险管控

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Textual 学习曲线 | 中 | 中 | 参考官方示例，复用现有组件 |
| 跨平台兼容性 | 低 | 高 | 优先保证 Linux，后测试 Windows/macOS |
| 性能问题 | 中 | 中 | 每任务完成后做性能测试 |
| 依赖冲突 | 低 | 中 | 使用虚拟环境，锁定版本 |

---

_创建时间：2026-04-02 22:37 | 版本：v1.0_
