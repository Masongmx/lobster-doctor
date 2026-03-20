#!/usr/bin/env env python3
"""
🦞 Lobster Doctor — 龙虾 workspace 健康管理

诊断 + 治疗 + 预防：解决 OpenClaw 长期使用后的文件膨胀问题。

命令：
  check       体检：扫描 workspace 健康状况
  cleanup     治疗：安全自动清理（清理前自动备份）
  cron-audit  巡检：检测 cron 僵尸任务
  stats       统计：workspace 文件分布概览
"""

import json
import os
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timedelta

# ==================== 路径配置 ====================
WORKSPACE = Path.home() / ".openclaw" / "workspace"
CRON_JOBS = Path.home() / ".openclaw" / "cron" / "jobs.json"
BACKUP_DIR = WORKSPACE / ".cleanup-backup"

# 核心文件白名单（永不删除）
CORE_FILES = {
    "AGENTS.md", "SOUL.md", "USER.md", "MEMORY.md", "TOOLS.md",
    "HEARTBEAT.md", "IDENTITY.md", "PROGRESS.md", "INTEL-DIRECTIVE.md",
    "BOOTSTRAP.md", "KB-SYNC-GUIDE.md", "package.json", "package-lock.json",
    ".env", ".openclaw", ".git", ".gitignore",
    ".model_override", ".openclaw-model-override",
}

# 受保护目录（不扫描不清理）
PROTECTED_DIRS = {"skills", "node_modules", ".git", "memory-tree", "memory"}

# 清理规则
STALE_DAYS_PY_JS_HTML = 3     # .py/.js/.html 超过N天未修改视为废弃
STALE_DAYS_MD = 7             # 根目录非核心 .md 超过N天未修改需要确认
MEMORY_LOG_MAX_DAYS = 30      # memory/ 日志保留天数
LARGE_FILE_THRESHOLD = 1 * 1024 * 1024  # 1MB


def load_json(path, default=None):
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default or {}
    return default or {}


def file_hash(path):
    """计算文件内容 MD5"""
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except (IOError, OSError):
        return None


def file_age_days(path):
    """文件最后修改距今天数"""
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return (datetime.now() - mtime).days
    except OSError:
        return 0


def estimate_tokens(text):
    """粗略估算 token 数（字符/4）"""
    return len(text) // 4


def fmt_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/1024/1024:.1f}MB"
    else:
        return f"{size_bytes/1024/1024/1024:.1f}GB"


# ==================== 体检 ====================

def cmd_check():
    print(f"🦞 龙虾医生 — 体检报告 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")

    issues = []
    total_files = 0
    total_size = 0

    # 1. 根目录扫描
    root_files = [f for f in WORKSPACE.iterdir() if f.is_file() and not f.name.startswith('.')]
    non_core = [f for f in root_files if f.name not in CORE_FILES]
    total_files += len(list(WORKSPACE.rglob('*')))

    print(f"📁 根目录: {len(root_files)} 个文件, {len(non_core)} 个非核心文件")
    if non_core:
        print(f"   非核心文件:")
        for f in sorted(non_core):
            age = file_age_days(f)
            size = fmt_size(f.stat().st_size)
            marker = "⚠️" if age > 7 else "  "
            print(f"   {marker} {f.name:40s} {size:>8s}  {age}天前修改")
            if age > 7:
                issues.append(f"根目录过期文件: {f.name} ({age}天)")
    print()

    # 2. 废弃文件检测
    stale_extensions = {'.py', '.js', '.html', '.txt', '.log'}
    stale_files = []
    for f in WORKSPACE.rglob('*'):
        if not f.is_file():
            continue
        # 跳过受保护目录
        if any(part in PROTECTED_DIRS for part in f.relative_to(WORKSPACE).parts):
            continue
        if f.suffix in stale_extensions:
            age = file_age_days(f)
            if age > STALE_DAYS_PY_JS_HTML:
                stale_files.append((f, age))
    total_size_stale = sum(f.stat().st_size for f, _ in stale_files)
    print(f"🗑️ 废弃文件 (>{STALE_DAYS_PY_JS_HTML}天): {len(stale_files)} 个, 共 {fmt_size(total_size_stale)}")
    for f, age in sorted(stale_files, key=lambda x: x[1], reverse=True)[:10]:
        rel = f.relative_to(WORKSPACE)
        print(f"   {age:3d}天  {str(rel)}")
    if len(stale_files) > 10:
        print(f"   ... 还有 {len(stale_files)-10} 个")
    if stale_files:
        issues.append(f"发现 {len(stale_files)} 个废弃文件")
    print()

    # 3. 重复文件检测
    hash_map = {}
    duplicates = []
    for f in WORKSPACE.rglob('*'):
        if not f.is_file() or f.stat().st_size == 0:
            continue
        if any(part in PROTECTED_DIRS for part in f.parts):
            continue
        h = file_hash(f)
        if h:
            if h in hash_map:
                duplicates.append((hash_map[h], f))
            else:
                hash_map[h] = f
    print(f"📋 重复文件: {len(duplicates)} 对")
    for orig, dup in sorted(duplicates, key=lambda x: str(x[0]))[:10]:
        print(f"   {orig.relative_to(WORKSPACE)}")
        print(f"   ↳ 重复: {dup.relative_to(WORKSPACE)}")
    if duplicates:
        issues.append(f"发现 {len(duplicates)} 对重复文件")
    print()

    # 4. 空目录检测
    empty_dirs = []
    for d in WORKSPACE.rglob('*'):
        if not d.is_dir():
            continue
        if any(part in PROTECTED_DIRS for part in d.parts):
            continue
        try:
            if not any(d.iterdir()):
                empty_dirs.append(d)
        except PermissionError:
            pass
    print(f"📂 空目录: {len(empty_dirs)} 个")
    for d in empty_dirs[:10]:
        print(f"   {d.relative_to(WORKSPACE)}")
    if empty_dirs:
        issues.append(f"发现 {len(empty_dirs)} 个空目录")
    print()

    # 5. 大文件检测
    large_files = []
    for f in WORKSPACE.rglob('*'):
        if not f.is_file():
            continue
        if any(part in PROTECTED_DIRS for part in f.parts):
            continue
        try:
            size = f.stat().st_size
            if size > LARGE_FILE_THRESHOLD:
                large_files.append((f, size))
        except OSError:
            pass
    large_files.sort(key=lambda x: x[1], reverse=True)
    print(f"📦 大文件 (>{fmt_size(LARGE_FILE_THRESHOLD)}): {len(large_files)} 个")
    total_large = sum(s for _, s in large_files)
    for f, size in large_files[:5]:
        print(f"   {fmt_size(size):>8s}  {f.relative_to(WORKSPACE)}")
    if len(large_files) > 5:
        print(f"   ... 还有 {len(large_files)-5} 个, 共 {fmt_size(total_large)}")
    if large_files:
        issues.append(f"发现 {len(large_files)} 个大文件, 共 {fmt_size(total_large)}")
    print()

    # 6. Bootstrap Context Token 估算
    bootstrap_files = [WORKSPACE / name for name in CORE_FILES if (WORKSPACE / name).is_file()]
    bootstrap_chars = 0
    for f in bootstrap_files:
        try:
            bootstrap_chars += len(f.read_text(encoding='utf-8'))
        except:
            pass
    bootstrap_tokens = estimate_tokens(str(bootstrap_chars))
    print(f"🧠 Bootstrap Context: ~{bootstrap_tokens:,} tokens ({bootstrap_chars:,} 字符)")
    if bootstrap_tokens > 8000:
        issues.append(f"Bootstrap context 过大: ~{bootstrap_tokens} tokens (建议 <8000)")
        print(f"   ⚠️ 偏大，建议精简 workspace 文件以节省 token")
    else:
        print(f"   ✅ 健康范围")
    print()

    # 7. Cron 僵尸检测
    cron_data = load_json(CRON_JOBS)
    if isinstance(cron_data, list):
        jobs = cron_data
    elif isinstance(cron_data, dict):
        jobs = cron_data.get("jobs", [])
    else:
        jobs = []
    cron_issues = 0
    if jobs:
        print(f"⏰ Cron 任务: {len(jobs)} 个")
        for job in jobs:
            name = job.get("name", "?")
            enabled = job.get("enabled", True)
            state = job.get("state", {})
            if not enabled:
                cron_issues += 1
                print(f"   ❌ 已禁用: {name}")
            elif any(kw in name.lower() for kw in ["test", "debug", "tmp", "temp"]):
                cron_issues += 1
                print(f"   ⚠️ 疑似临时: {name}")
            else:
                print(f"   ✅ {name}")
        if cron_issues:
            issues.append(f"发现 {cron_issues} 个可疑 cron 任务")
    else:
        print(f"⏰ Cron 任务: 无")
    print()

    # 8. 记忆树状态（如果安装了）
    mt_script = WORKSPACE / "skills" / "memory-tree" / "scripts" / "memory_tree.py"
    if mt_script.exists():
        print("🌳 记忆树: 已安装")
        print(f"   运行 `lobster_doctor.py check` 后可执行:")
        print(f"   python3 skills/memory-tree/scripts/memory_tree.py visualize")
    else:
        print("🌳 记忆树: 未安装")
    print()

    # 总结
    if issues:
        print(f"{'='*50}")
        print(f"🔍 发现 {len(issues)} 个问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print()
        print(f"💡 运行 `lobster_doctor.py cleanup` 自动修复（清理前会备份）")
    else:
        print(f"{'='*50}")
        print(f"✅ workspace 健康状况良好！")


# ==================== 清理 ====================

def cmd_cleanup(dry_run=False):
    if dry_run:
        print(f"🦞 龙虾医生 — 模拟清理 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")
    else:
        print(f"🦞 龙虾医生 — 自动清理 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")

    # 创建备份目录
    today = datetime.now().strftime('%Y-%m-%d')
    backup = BACKUP_DIR / today
    if not dry_run:
        backup.mkdir(parents=True, exist_ok=True)

    deleted_files = 0
    deleted_dirs = 0
    skipped = []
    freed_bytes = 0

    # 1. 清理根目录废弃脚本
    stale_extensions = {'.py', '.js', '.html', '.txt', '.log', '.json'}
    for f in list(WORKSPACE.iterdir()):
        if not f.is_file() or f.name in CORE_FILES:
            continue
        if f.name.startswith('.'):
            continue
        if f.suffix in stale_extensions and file_age_days(f) > STALE_DAYS_PY_JS_HTML:
            size = f.stat().st_size
            rel = f.relative_to(WORKSPACE)
            if dry_run:
                print(f"  🗑️ [模拟] {rel} ({fmt_size(size)})")
            else:
                try:
                    f.rename(backup / f.name)
                    print(f"  🗑️ {rel} → 备份 ({fmt_size(size)})")
                except OSError as e:
                    skipped.append((rel, str(e)))
                    continue
            deleted_files += 1
            freed_bytes += size

    # 2. 清理 .tmp/.bak 文件
    for f in WORKSPACE.rglob('*'):
        if not f.is_file():
            continue
        if any(part in PROTECTED_DIRS for part in f.parts):
            continue
        if f.suffix in {'.tmp', '.bak', '.old', '.swp'}:
            size = f.stat().st_size
            rel = f.relative_to(WORKSPACE)
            if dry_run:
                print(f"  🗑️ [模拟] {rel} ({fmt_size(size)})")
            else:
                try:
                    dest = backup / f.name
                    if dest.exists():
                        dest = backup / f"{f.name}_{id(f)}"
                    f.rename(dest)
                    print(f"  🗑️ {rel} → 备份 ({fmt_size(size)})")
                except OSError as e:
                    skipped.append((rel, str(e)))
                    continue
            deleted_files += 1
            freed_bytes += size

    # 3. 清理空目录
    for d in list(WORKSPACE.rglob('*')):
        if not d.is_dir() or d == WORKSPACE:
            continue
        if any(part in PROTECTED_DIRS for part in d.parts):
            continue
        try:
            if not any(d.iterdir()):
                rel = d.relative_to(WORKSPACE)
                if dry_run:
                    print(f"  📂 [模拟] 空目录: {rel}")
                else:
                    d.rmdir()
                    print(f"  📂 空目录已删除: {rel}")
                deleted_dirs += 1
        except (OSError, PermissionError):
            pass

    # 4. 清理过期 memory 日志
    memory_dir = WORKSPACE / "memory"
    if memory_dir.exists():
        cutoff = datetime.now() - timedelta(days=MEMORY_LOG_MAX_DAYS)
        for f in memory_dir.glob('*.md'):
            if f.name == 'README.md' or f.name == 'heartbeat-state.json':
                continue
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    size = f.stat().st_size
                    rel = f.relative_to(WORKSPACE)
                    if dry_run:
                        print(f"  📝 [模拟] 过期日志: {rel} ({file_age_days(f)}天)")
                    else:
                        f.rename(backup / f.name)
                        print(f"  📝 过期日志已归档: {rel} ({file_age_days(f)}天, {fmt_size(size)})")
                    deleted_files += 1
                    freed_bytes += size
            except OSError:
                pass

    # 5. 清理重复文件
    hash_map = {}
    for f in WORKSPACE.rglob('*'):
        if not f.is_file() or f.stat().st_size == 0:
            continue
        if any(part in PROTECTED_DIRS for part in f.parts):
            continue
        h = file_hash(f)
        if h:
            if h in hash_map:
                orig, dup = hash_map[h], f
                size = dup.stat().st_size
                rel = dup.relative_to(WORKSPACE)
                if dry_run:
                    print(f"  📋 [模拟] 重复文件: {rel} (与 {orig.relative_to(WORKSPACE)} 相同)")
                else:
                    try:
                        dup.rename(backup / f"{dup.name}_{id(dup)}")
                        print(f"  📋 重复文件已移除: {rel}")
                    except OSError as e:
                        skipped.append((rel, str(e)))
                deleted_files += 1
                freed_bytes += size
            else:
                hash_map[h] = f

    # 总结
    print(f"\n{'='*50}")
    mode = "模拟" if dry_run else "实际"
    print(f"🧹 {mode}清理完成:")
    print(f"   📄 删除文件: {deleted_files}")
    print(f"   📂 删除空目录: {deleted_dirs}")
    print(f"   💾 释放空间: {fmt_size(freed_bytes)}")
    if skipped:
        print(f"   ⚠️ 跳过 {len(skipped)} 个:")
        for rel, reason in skipped:
            print(f"      {rel}: {reason}")
    if not dry_run and (deleted_files > 0 or deleted_dirs > 0):
        print(f"   📦 备份位置: {backup}")


# ==================== Cron 巡检 ====================

def cmd_cron_audit():
    print(f"🦞 龙虾医生 — Cron 巡检 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")

    cron_data = load_json(CRON_JOBS)
    if isinstance(cron_data, list):
        jobs = cron_data
    elif isinstance(cron_data, dict):
        jobs = cron_data.get("jobs", [])
    else:
        jobs = []

    if not jobs:
        print("📭 没有 cron 任务")
        return

    print(f"⏰ 共 {len(jobs)} 个 cron 任务\n")

    healthy = 0
    warnings = []

    for i, job in enumerate(jobs, 1):
        name = job.get("name", f"#{i}")
        enabled = job.get("enabled", True)
        schedule = job.get("schedule", {})
        expr = schedule.get("expr", "?")
        session = job.get("sessionTarget", "?")
        created = job.get("createdAtMs", 0)
        state = job.get("state", {})
        next_run = state.get("nextRunAtMs")

        # 状态图标
        if not enabled:
            status = "❌ 禁用"
            warnings.append(f"{name}: 已禁用，建议删除")
        elif any(kw in name.lower() for kw in ["test", "debug", "tmp", "temp", "old"]):
            status = "⚠️ 疑似临时"
            warnings.append(f"{name}: 名称含 test/debug/tmp，可能是临时任务")
        else:
            status = "✅ 正常"
            healthy += 1

        # 创建时间
        if created:
            created_date = datetime.fromtimestamp(created / 1000).strftime('%Y-%m-%d')
            age_days = (datetime.now() - datetime.fromtimestamp(created / 1000)).days
        else:
            created_date = "未知"
            age_days = 0

        print(f"  {status} {name}")
        print(f"      调度: {expr} | 目标: {session} | 创建: {created_date} ({age_days}天前)")
        if next_run:
            next_date = datetime.fromtimestamp(next_run / 1000).strftime('%Y-%m-%d %H:%M')
            print(f"      下次运行: {next_date}")
        print()

    # 检查运行历史
    runs_dir = Path.home() / ".openclaw" / "cron" / "runs"
    if runs_dir.exists():
        run_files = list(runs_dir.glob("*.jsonl"))
        print(f"📊 运行历史: {len(run_files)} 条记录")

    print(f"\n{'='*50}")
    print(f"  ✅ 健康: {healthy}  |  ⚠️ 警告: {len(warnings)}")
    if warnings:
        print(f"\n  建议操作:")
        for w in warnings:
            print(f"  • {w}")
        print(f"\n  删除命令: openclaw cron rm <job-id>")


# ==================== 统计 ====================

def cmd_stats():
    print(f"🦞 龙虾医生 — Workspace 统计 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")

    total_files = 0
    total_size = 0
    ext_stats = {}
    dir_stats = {}

    for f in WORKSPACE.rglob('*'):
        if not f.is_file():
            continue
        total_files += 1
        try:
            size = f.stat().st_size
            total_size += size
        except OSError:
            size = 0

        ext = f.suffix.lower() or '.无后缀'
        ext_stats[ext] = ext_stats.get(ext, {"count": 0, "size": 0})
        ext_stats[ext]["count"] += 1
        ext_stats[ext]["size"] += size

        # 目录统计
        parent = f.parent.name
        if parent not in dir_stats:
            dir_stats[parent] = {"count": 0, "size": 0}
        dir_stats[parent]["count"] += 1
        dir_stats[parent]["size"] += size

    print(f"📂 总计: {total_files} 个文件, {fmt_size(total_size)}\n")

    # 按后缀分类
    print("📊 按类型:")
    sorted_exts = sorted(ext_stats.items(), key=lambda x: x[1]["size"], reverse=True)
    for ext, data in sorted_exts[:15]:
        bar = "█" * min(20, data["size"] // (total_size // 20 + 1))
        print(f"  {ext:12s} {data['count']:4d}个 {fmt_size(data['size']):>8s} {bar}")
    print()

    # 按目录分类
    print("📁 按目录:")
    sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[1]["size"], reverse=True)
    for name, data in sorted_dirs[:10]:
        if name in PROTECTED_DIRS:
            continue
        print(f"  {name:25s} {data['count']:4d}个 {fmt_size(data['size']):>8s}")
    print()

    # 技能统计
    skills_dir = WORKSPACE / "skills"
    if skills_dir.exists():
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        print(f"🧩 已安装技能: {len(skill_dirs)} 个")
        for s in sorted(skill_dirs, key=lambda x: x.name)[:10]:
            sk_files = list(s.rglob('*'))
            sk_size = sum(f.stat().st_size for f in sk_files if f.is_file())
            print(f"  {s.name:30s} {len(sk_files):3d}个文件 {fmt_size(sk_size):>8s}")
        if len(skill_dirs) > 10:
            print(f"  ... 还有 {len(skill_dirs)-10} 个")
        print()

    # Memory 目录统计
    memory_dir = WORKSPACE / "memory"
    if memory_dir.exists():
        mem_files = list(memory_dir.glob('*.md'))
        mem_size = sum(f.stat().st_size for f in mem_files if f.is_file())
        print(f"📝 记忆日志: {len(mem_files)} 个, {fmt_size(mem_size)}")


# ==================== CLI ====================

def main():
    if len(sys.argv) < 2:
        print("🦞 Lobster Doctor — 龙虾 workspace 健康管理\n")
        print("命令:")
        print("  check              体检：扫描 workspace 健康状况")
        print("  cleanup            治疗：安全自动清理（清理前自动备份）")
        print("  cleanup --dry-run  模拟清理（只报告不删除）")
        print("  cron-audit         巡检：检测 cron 僵尸任务")
        print("  stats              统计：workspace 文件分布概览")
        print("  skill-slim report  技能瘦身：token 消耗报告（不修改）")
        print("  skill-slim dry-run 技能瘦身：预览精简效果（不修改）")
        print("  skill-slim apply   技能瘦身：应用精简（自动备份）")
        print()
        print("建议: 每周运行一次 check，每月运行一次 cleanup")
        return

    cmd = sys.argv[1]
    if cmd == "check":
        cmd_check()
    elif cmd == "cleanup":
        dry_run = "--dry-run" in sys.argv
        cmd_cleanup(dry_run=dry_run)
    elif cmd == "cron-audit":
        cmd_cron_audit()
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "skill-slim":
        # 委托给 skill_slim.py
        from skill_slim import main as skill_slim_main
        sys.argv = [sys.argv[0], *sys.argv[2:]]  # 去掉 skill-slim
        skill_slim_main()
    else:
        print(f"❌ 未知命令: {cmd}")
        print("运行 `lobster_doctor.py` 查看可用命令")


if __name__ == "__main__":
    main()
