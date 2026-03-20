# Security Statement

## Why ClawHub Flagged This Skill

ClawHub Security may flag `lobster-doctor` due to these patterns:

### 1. File Deletion (cleanup command)
The `cleanup` command removes stale files from workspace. **However:**
- Requires `--dry-run` preview first
- Automatically backs up to `.cleanup-backup/YYYY-MM-DD/`
- Core files are whitelist-protected (SOUL.md, MEMORY.md, etc.)
- Protected directories: `skills/`, `node_modules/`, `memory/`

### 2. File Modification (skill-slim command)
The `skill-slim` command modifies other skills' SKILL.md files. **However:**
- `report` and `dry-run` are read-only
- `apply` creates backups in `.cleanup-backup/skill-slim/`
- The skill itself is whitelisted (won't modify itself)

### 3. Cron Access (cron-audit command)
Reads `~/.openclaw/cron/jobs.json` to detect zombie tasks. **Read-only operation.**

## What This Skill Does NOT Do

- ❌ No network access
- ❌ No external API calls
- ❌ No data exfiltration
- ❌ No code execution from external sources
- ❌ No hidden payloads

## Dependencies

**Zero external dependencies.** Uses only Python standard library:
- `json`, `os`, `hashlib`, `sys`, `pathlib`, `datetime`

## Verdict

🟢 **SAFE TO INSTALL**

This is a legitimate workspace health management tool. All "dangerous" operations require explicit user confirmation and include backup mechanisms.

If you have concerns, review the source code:
- `scripts/lobster_doctor.py` - Main tool
- `scripts/skill_slim.py` - Skill slimming utility
