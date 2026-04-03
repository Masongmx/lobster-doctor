# 🦞 Lobster Doctor

[![OpenClaw](https://img.shields.io/badge/OpenClaw-%3E%3D0.3.0-blue)](https://github.com/Masongmx/openclaw)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-v4.2.0-green)](https://github.com/Masongmx/openclaw/tree/main/skills/lobster-doctor)

> **Pack it, Run it, Clean it.**
> 
> 装得下，用得久，清得掉。

OpenClaw's workspace health guardian. Monitor session health, detect orphaned processes, archive old memories, and keep your agent running longer and smoother.

[中文文档](SKILL.md) | [Detailed Guide](KNOWLEDGE.md)

---

## ✨ Features

- **🧠 Smart Memory Management** — Archive old memories to extend session lifespan
- **📊 Relative Threshold Alerts** — Token warnings based on model context window, not fixed values
- **🛡️ Safe Cleanup** — Whitelist protection + automatic backups + one-click undo
- **🔍 Health Diagnostics** — Comprehensive workspace health checks with actionable recommendations
- **🖥️ System Health Check** — NEW! Monitor workspace size, hidden folders, and structural violations
- **🧹 System Cleanup** — NEW! 3-phase cleanup with backup and undo support
- **⚡ Zero-Token Operation** — Runs locally without LLM calls
- **🔄 Scheduled Maintenance** — Automatic weekly health checks (Wed 06:00)

---

## 📦 Installation

```bash
# Install via ClawHub
clawhub install lobster-doctor

# Or clone manually
cd ~/.openclaw/workspace/skills
git clone https://github.com/Masongmx/openclaw.git lobster-doctor
```

---

## 🚀 Quick Start

```bash
# From anywhere - find and run
SKILL_DIR=$(find ~/.openclaw ~/.npm-global -name "lobster-doctor" -type d 2>/dev/null | head -1)
python3 "$SKILL_DIR/scripts/lobster_doctor.py" health

# Or cd to skill directory first
cd ~/.openclaw/workspace/skills/lobster-doctor
python3 scripts/lobster_doctor.py health
```

---

## 🆕 What's New in v4.2.0

### 🖥️ TUI (Terminal User Interface)

**New!** Visual workspace health monitor with real-time status display.

```bash
# Find skill location and launch TUI
SKILL_DIR=$(find ~/.openclaw ~/.npm-global -name "lobster-doctor" -type d 2>/dev/null | head -1)
python3 "$SKILL_DIR/scripts/lobster_tui.py"

# Or if you know the location:
cd ~/.openclaw/workspace/skills/lobster-doctor
python3 scripts/lobster_tui.py
```

**Skill may be installed at**:
- User skill: `~/.openclaw/workspace/skills/lobster-doctor`
- System skill: `~/.npm-global/lib/node_modules/openclaw/skills/lobster-doctor`

**Interface Overview**:
```
┌─────────────────────────────────────────────────────────────────┐
│ 🦞 Lobster Doctor  │  🟢 Healthy  │  16.7MB  │  📁 5  │ 🕐 22:51 │
├─────────────────────────────────────────────────────────────────┤
│  ┌── Sessions ─────────┐  ┌── Files ────────┐  ┌── Skills ─────┐│
│  │ Total Sessions: 3   │  │ Hidden: 5 🟢    │  │ Total: 47     ││
│  │ Active: 2           │  │ Large: 0 🟢     │  │ Tokens: 150K  ││
│  │ Token: 250K/1M 25%  │  │ Violations: 0   │  │ Avg: 3,191    ││
│  │ [██████░░░░░░░] 🟢  │  │ Waste: 0B       │  │ Largest:      ││
│  └─────────────────────┘  └─────────────────┘  │ deep-research ││
│                                                └───────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ [A]rchive [S]lim [C]leanup [H]ealth [R]efresh [Q]uit            │
└─────────────────────────────────────────────────────────────────┘
```

**Keyboard Shortcuts**:

| Key | Action | Description |
|-----|--------|-------------|
| `A` | Archive | Archive old memories |
| `S` | Slim | Trim skill descriptions |
| `C` | Cleanup | Safe cleanup of obsolete files |
| `H` | Health | Run comprehensive health check |
| `R` | Refresh | Manual refresh all panels |
| `Q` | Quit | Exit TUI safely |

**Health Status Colors**:

| Icon | Workspace Size | Status |
|------|----------------|--------|
| 🟢 | < 500MB | Healthy |
| 🟡 | 500MB - 1GB | Attention needed |
| 🔴 | > 1GB | Danger - immediate cleanup |

**Features**:
- **Real-time Monitoring** — 5-second auto-refresh
- **Three-panel Layout** — Sessions, Files, Skills
- **One-key Actions** — Trigger commands instantly
- **Color-coded Status** — Visual health indicators

**Requirements**:
```bash
pip install textual>=8.0.0 rich>=13.0.0
```

See [TUI User Guide](docs/tui-user-guide.md) for detailed documentation.

---

## What's New in v4.1.0

### System Health Check
```bash
# Check workspace structure (say: "check workspace health")
python3 scripts/lobster_doctor.py system-health
```

**Output:**
- Workspace size (target: <500MB 🟢)
- Hidden folder count (target: <15 🟢)
- Large files (>50MB)
- Structural violations (multi-workspace, duplicate configs)

### System Cleanup
```bash
# Clean workspace (say: "clean up workspace")
python3 scripts/lobster_doctor.py system-cleanup
```

**3-Phase Cleanup:**
1. **Phase 1**: Safe cleanup (temp files, node_modules, reference/)
2. **Phase 2**: Structure fix (migrate archive, remove duplicate configs)
3. **Phase 3**: Deep cleanup (AI tool residuals, old backups)

**Safety:**
- Auto backup to `.cleanup-backup/`
- Whitelist protection (core files never deleted)
- Undo support: `python3 scripts/lobster_doctor.py cleanup --undo`

### Claude Code Design Principles
Integrated 7 core principles from Claude Code architecture:
1. Don't trust model自觉性 → Institutionalize behavior
2. Separate roles → main/reviewer/developer
3. Tool governance → 14-step pipeline
4. Context is budget → Workspace size limits
5. Security layers don't bypass → 3-layer protection
6. Ecosystem needs model awareness → Natural language triggers
7. Productization handles Day 2 → Cleanup chain + cron

---

## 📖 Commands Reference

| Command | Priority | Description |
|---------|----------|-------------|
| `health` | **P0** | Comprehensive workspace diagnostics |
| `archive` | **P0** | Archive old memory files to extend sessions |
| `session` | **P1** | Token usage monitoring with relative thresholds |
| `cleanup` | **P1** | Safe cleanup of obsolete files |
| `slim` | **P2** | Trim skill descriptions for efficiency |
| `system-health` | **P1** | System体检 (folder structure + size analysis) |
| `system-cleanup` | **P1** | Integrated cleanup workflow |

### Health Check

```bash
python3 scripts/lobster_doctor.py health [--json]
```

Output includes:
- Memory file count and total lines
- Session health status
- Skill usage statistics
- Orphaned process detection

### Archive Memory

```bash
# Archive files older than 30 days (default)
python3 scripts/lobster_doctor.py archive

# Custom retention period
python3 scripts/lobster_doctor.py archive --days 60

# Undo last archive
python3 scripts/lobster_doctor.py archive --undo
```

### Session Check

```bash
python3 scripts/lobster_doctor.py session [--json]
```

Shows each session's:
- Token usage percentage
- Health status (healthy/attention/warning/danger)
- Recommended actions

### Safe Cleanup

```bash
# Clean obsolete files
python3 scripts/lobster_doctor.py cleanup

# Undo last cleanup
python3 scripts/lobster_doctor.py cleanup --undo
```

---

## ⚙️ Configuration

### Relative Thresholds

Based on model context window percentages, not fixed values:

| Status | Threshold | Action |
|--------|-----------|--------|
| 🟢 Healthy | <50% | Plenty of space |
| 🟡 Attention | 50-70% | Start monitoring |
| ⚠️ Warning | 70-85% | Take action |
| 🔴 Danger | >85% | Immediate attention |

**Benefits**: Automatically adapts to different models (GPT-4o 128K, Claude 200K, etc.)

### Whitelist Protection

Core files are never deleted:
- `MEMORY.md`
- `SOUL.md`
- `IDENTITY.md`
- `USER.md`
- `AGENTS.md`
- `PROGRESS.md`
- `rules/common/*.md`

### Scheduled Tasks

```json
{
  "autoRun": {
    "command": "health",
    "schedule": "0 8 * * *"
  }
}
```

---

## 🔒 Safety Mechanisms

| Mechanism | Description |
|-----------|-------------|
| **Whitelist** | Core files are never deleted |
| **Auto-backup** | Automatic backup to `.cleanup-backup/` |
| **One-click Undo** | `--undo` flag restores from backup |
| **Relative Thresholds** | Adapts to model context windows |
| **Zero Token** | Pure local execution, no LLM calls |

---

## 💬 Natural Language Triggers

| What You Say | What Agent Does |
|--------------|-----------------|
| "Check my health" | Run comprehensive health check |
| "Archive old memories" | Archive expired memory files |
| "How's my token usage" | Check session token usage |
| "Slim down my skills" | Trim skill descriptions |
| "Clean up my workspace" | Safe cleanup of obsolete files |
| "System体检" | Run system health diagnostics |

---

## 📊 Sample Output

```
🦞 Lobster Doctor — Health Check (2026-03-26 18:15)

🔴 Sessions: 36 sessions, ~1.9M tokens (1452.5%)
   Context window: 128K tokens
   Remaining: ~-1731198 tokens
   🚨 Danger sessions: 4
   ⚠️  Warning sessions: 1

📦 Obsolete files: 1 file, 20.6KB

🧩 Skills: 102 skills, description ~3K tokens

🧠 Bootstrap: ~101K tokens

⚠️ Found 3 issues:
   🔴 Danger sessions: 4
   🟡 Warning sessions: 1
   🧠 Bootstrap oversized: ~101K tokens
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 Changelog

- **v4.2.0** — TUI MVP release. Visual workspace health monitor with Textual + Rich
- **v4.1.0** — System health/cleanup commands, Claude Code design principles
- **v4.0.0** — Repositioned as "Pack it, Run it, Clean it". Added memory archiving, relative thresholds, orphaned process detection
- **v3.0.0** — Streamlined to 4 core commands. Agent-triggered health checks
- **v2.2.0** — Token monitoring alerts, Feishu push fixes
- **v2.0.0** — Session health monitoring, weekly reports

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Related

- [OpenClaw](https://github.com/Masongmx/openclaw) — The main framework
- [ClawHub](https://github.com/Masongmx/openclaw) — Skill registry

---

<p align="center">
  Made with 🦞 by <a href="https://github.com/Masongmx">Masongmx</a>
</p>