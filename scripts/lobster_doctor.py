#!/usr/bin/env env python3
"""
🦞 Lobster Doctor v4.0 — 装得下，用得久，清得掉

会话监控 + Memory 归档 + 安全清理。纯本地运行，零成本。

核心价值：
- 装得下：技能瘦身，减少每轮注入量
- 用得久：会话监控，相对阈值告警
- 清得掉：安全清理，白名单保护

命令：
  archive       Memory 归档：归档旧记忆，延长会话续航
  session       会话检查：检查会话历史大小，相对阈值告警
  cleanup       安全清理：清理废弃文件，白名单保护
  slim          技能瘦身：精简 description，省 token
  health        健康检查：Agent 定期执行，发现问题推送

v4.0 变更：
  - 重新定位"装得下，用得久，清得掉"
  - 新增 Memory 归档（P0 核心）
  - 使用相对阈值（基于模型上下文窗口）
  - 新增孤立进程检测、内存泄漏警告、Token 计数器验证
  - 所有命令零 Token 消耗
"""

import json
import os
import hashlib
import sys
import re
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 导入公共模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common"))
from utils import (
    load_json, save_json, file_hash, file_age_days,
    estimate_tokens, fmt_tokens, fmt_size,
    WORKSPACE, OPENCLAW_CONFIG
)

# ==================== 路径配置 ====================
CRON_JOBS = Path.home() / ".openclaw" / "cron" / "jobs.json"
BACKUP_DIR = WORKSPACE / ".cleanup-backup"
ARCHIVE_DIR = Path.home() / ".openclaw" / "archive"

# 相对阈值设计（基于模型上下文窗口百分比）
# 不同模型的上下文窗口大小
MODEL_CONTEXT_WINDOWS = {
    "gpt-4o": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    "gpt-3.5-turbo": 16_385,
    "claude-3-opus": 200_000,
    "claude-3-sonnet": 200_000,
    "claude-3-haiku": 200_000,
    "claude-2": 100_000,
    "glm-4": 128_000,
    "glm-5": 128_000,
    "qwen3": 32_000,
    "qwen2.5": 32_000,
    "default": 128_000,  # 默认假设128K
}

# 阈值百分比配置
THRESHOLD_PERCENTAGES = {
    "healthy": 0.50,   # < 50% 健康
    "notice": 0.70,    # 50-70% 注意
    "warning": 0.85,   # 70-85% 警告
    "danger": 0.95,    # > 85% 危险
}

# 会话健康阈值（绝对值，用于兼容旧代码）
SESSION_WARN_THRESHOLD = 100_000   # 100K tokens 告警
SESSION_DANGER_THRESHOLD = 200_000 # 200K tokens 强烈告警

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
MEMORY_LOG_MAX_DAYS = 30      # memory/ 日志保留天数


# ==================== 相对阈值计算 ====================

def get_model_context_window(model_name=None):
    """
    获取模型的上下文窗口大小
    
    Args:
        model_name: 模型名称，如 "gpt-4o", "claude-3-opus"
    
    Returns:
        int: 上下文窗口大小（tokens）
    """
    if model_name is None:
        # 尝试从配置读取当前模型
        try:
            config = load_json(OPENCLAW_CONFIG)
            model_name = config.get("model", {}).get("default", "default")
        except Exception:
            model_name = "default"
    
    # 标准化模型名称
    model_lower = model_name.lower() if model_name else "default"
    
    # 匹配模型
    for key, window in MODEL_CONTEXT_WINDOWS.items():
        if key in model_lower:
            return window
    
    return MODEL_CONTEXT_WINDOWS["default"]


def calculate_relative_threshold(tokens_used, model_name=None):
    """
    计算相对阈值状态
    
    Args:
        tokens_used: 当前使用的 token 数
        model_name: 模型名称
    
    Returns:
        dict: {"status": "healthy|notice|warning|danger", "percentage": xx.x, "remaining": xxx}
    """
    window = get_model_context_window(model_name)
    percentage = tokens_used / window
    remaining = window - tokens_used
    
    if percentage < THRESHOLD_PERCENTAGES["healthy"]:
        status = "healthy"
    elif percentage < THRESHOLD_PERCENTAGES["notice"]:
        status = "notice"
    elif percentage < THRESHOLD_PERCENTAGES["warning"]:
        status = "warning"
    else:
        status = "danger"
    
    return {
        "status": status,
        "percentage": round(percentage * 100, 1),
        "remaining": remaining,
        "window": window
    }


# ==================== 孤立进程检测 ====================

def detect_orphan_processes():
    """
    检测孤立的 OpenClaw 相关进程
    
    孤立进程定义：
    1. 已退出但留下僵尸进程
    2. 运行时间异常长（>24小时）的会话进程
    3. 重复的进程实例
    
    Returns:
        list: 检测到的孤立进程列表
    """
    orphans = []
    
    try:
        # 检查 OpenClaw 相关进程
        import subprocess
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        lines = result.stdout.strip().split('\n')
        openclaw_processes = []
        
        for line in lines:
            if any(kw in line.lower() for kw in ['openclaw', 'clawd', 'gateway']):
                parts = line.split()
                if len(parts) >= 11:
                    pid = parts[1]
                    cpu = parts[2]
                    mem = parts[3]
                    time = parts[9]
                    cmd = ' '.join(parts[10:])
                    
                    # 检查运行时间是否异常（超过24小时）
                    time_parts = time.split(':')
                    if len(time_parts) >= 2:
                        try:
                            hours = int(time_parts[0])
                            if hours > 24:
                                orphans.append({
                                    "type": "long_running",
                                    "pid": pid,
                                    "cpu": cpu,
                                    "mem": mem,
                                    "time": time,
                                    "cmd": cmd[:80],
                                    "reason": f"运行时间超过24小时 ({time})"
                                })
                        except ValueError:
                            pass
                    
                    openclaw_processes.append({
                        "pid": pid,
                        "cmd": cmd[:80]
                    })
        
        # 检查重复进程
        cmd_counts = {}
        for proc in openclaw_processes:
            cmd = proc["cmd"]
            if cmd not in cmd_counts:
                cmd_counts[cmd] = []
            cmd_counts[cmd].append(proc["pid"])
        
        for cmd, pids in cmd_counts.items():
            if len(pids) > 2:  # 超过2个相同进程可能是重复
                orphans.append({
                    "type": "duplicate",
                    "pids": pids,
                    "cmd": cmd[:80],
                    "reason": f"发现 {len(pids)} 个重复进程"
                })
    
    except Exception as e:
        orphans.append({
            "type": "error",
            "reason": f"检测失败: {str(e)}"
        })
    
    return orphans


# ==================== 内存泄漏警告 ====================

def check_memory_leak():
    """
    检查可能的内存泄漏
    
    检测项：
    1. 进程内存占用异常增长
    2. 会话历史文件异常膨胀
    3. 临时文件堆积
    
    Returns:
        dict: 内存泄漏检测结果
    """
    results = {
        "warnings": [],
        "memory_usage": {},
        "large_files": []
    }
    
    try:
        # 检查进程内存使用
        import subprocess
        result = subprocess.run(
            ["ps", "aux", "--sort=-%mem"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        lines = result.stdout.strip().split('\n')
        top_memory = []
        
        for line in lines[1:11]:  # 前10个内存占用最高的进程
            parts = line.split()
            if len(parts) >= 11:
                mem_percent = float(parts[3])
                if mem_percent > 10:  # 内存占用超过10%
                    top_memory.append({
                        "pid": parts[1],
                        "mem_percent": mem_percent,
                        "cmd": ' '.join(parts[10:])[:60]
                    })
        
        if top_memory:
            results["warnings"].append({
                "type": "high_memory_usage",
                "processes": top_memory,
                "message": f"发现 {len(top_memory)} 个高内存占用进程"
            })
        
        results["memory_usage"]["top_processes"] = top_memory
        
        # 检查会话历史文件大小
        agents_dir = Path.home() / ".openclaw" / "agents"
        large_session_files = []
        
        if agents_dir.exists():
            for session_file in agents_dir.rglob("*.jsonl"):
                try:
                    size_mb = session_file.stat().st_size / (1024 * 1024)
                    if size_mb > 10:  # 单个会话文件超过10MB
                        large_session_files.append({
                            "path": str(session_file.relative_to(agents_dir)),
                            "size_mb": round(size_mb, 1)
                        })
                except Exception:
                    pass
        
        if large_session_files:
            results["large_files"] = large_session_files
            results["warnings"].append({
                "type": "large_session_files",
                "files": large_session_files[:5],
                "message": f"发现 {len(large_session_files)} 个超大会话文件"
            })
        
        # 检查临时文件堆积
        tmp_dirs = [
            Path.home() / ".openclaw" / "tmp",
            Path("/tmp"),
        ]
        
        tmp_count = 0
        tmp_size = 0
        
        for tmp_dir in tmp_dirs:
            if tmp_dir.exists():
                for f in tmp_dir.glob("*"):
                    if f.name.startswith("openclaw") or f.name.startswith("claw"):
                        try:
                            tmp_count += 1
                            tmp_size += f.stat().st_size
                        except Exception:
                            pass
        
        if tmp_count > 50 or tmp_size > 100 * 1024 * 1024:  # 超过50个文件或100MB
            results["warnings"].append({
                "type": "temp_file_buildup",
                "count": tmp_count,
                "size_mb": round(tmp_size / (1024 * 1024), 1),
                "message": f"临时文件堆积: {tmp_count} 个文件, {round(tmp_size/(1024*1024), 1)}MB"
            })
    
    except Exception as e:
        results["warnings"].append({
            "type": "error",
            "message": f"检测失败: {str(e)}"
        })
    
    return results


# ==================== Token 计数器验证 ====================

def verify_token_counter():
    """
    验证 Token 计数器的准确性
    
    检测项：
    1. 会话历史中的 token 统计是否准确
    2. 模型返回的 usage 信息是否合理
    3. 是否存在 token 计数异常的会话
    
    Returns:
        dict: Token 计数器验证结果
    """
    results = {
        "status": "ok",
        "anomalies": [],
        "sessions_checked": 0,
        "total_tokens": 0
    }
    
    agents_dir = Path.home() / ".openclaw" / "agents"
    
    if not agents_dir.exists():
        return results
    
    for session_file in agents_dir.rglob("*.jsonl"):
        if ".reset." in session_file.name or ".deleted." in session_file.name:
            continue
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            results["sessions_checked"] += 1
            
            # 计算文件大小估算的 token 数
            file_size = session_file.stat().st_size
            estimated_tokens = file_size // 4
            
            # 检查是否包含 usage 信息
            actual_tokens = 0
            for line in lines[-10:]:  # 检查最后10行
                try:
                    data = json.loads(line)
                    # 检查是否有 usage 信息
                    if "usage" in data:
                        usage = data["usage"]
                        actual_tokens = usage.get("total_tokens", 0)
                        break
                except json.JSONDecodeError:
                    pass
            
            results["total_tokens"] += estimated_tokens
            
            # 检查异常
            if estimated_tokens > 500_000:  # 单个会话超过500K tokens
                results["anomalies"].append({
                    "type": "large_session",
                    "path": str(session_file.relative_to(agents_dir)),
                    "tokens": estimated_tokens,
                    "message": f"会话文件过大: ~{fmt_tokens(estimated_tokens)} tokens"
                })
            
            # 如果有实际 token 数，比较估算和实际
            if actual_tokens > 0:
                diff_percent = abs(estimated_tokens - actual_tokens) / actual_tokens
                if diff_percent > 0.5:  # 差异超过50%
                    results["anomalies"].append({
                        "type": "token_mismatch",
                        "path": str(session_file.relative_to(agents_dir)),
                        "estimated": estimated_tokens,
                        "actual": actual_tokens,
                        "diff_percent": round(diff_percent * 100, 1),
                        "message": f"Token 计数差异: 估算 {estimated_tokens}, 实际 {actual_tokens}"
                    })
        
        except Exception:
            pass
    
    if results["anomalies"]:
        results["status"] = "anomalies_found"
    
    return results


# ==================== Memory 归档 ====================

def cmd_archive(args):
    """
    Memory 归档命令
    
    归档规则：
    - 默认归档超过 30 天未修改的记忆
    - 永久标记（📌）的内容不归档
    - 归档到 ~/.openclaw/archive/
    """
    dry_run = getattr(args, 'dry_run', False)
    days = getattr(args, 'days', 30)
    
    results = {
        "archived": [],
        "skipped": [],
        "errors": [],
        "freed_tokens": 0
    }
    
    memory_md = WORKSPACE / "MEMORY.md"
    
    if not memory_md.exists():
        if getattr(args, 'json', False):
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print("❌ MEMORY.md 不存在")
        return results
    
    if dry_run:
        print(f"🦞 龙虾医生 — 模拟归档 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")
    else:
        print(f"🦞 龙虾医生 — Memory 归档 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")
    
    # 创建归档目录
    if not dry_run:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 检查 memory/ 目录下的文件
    memory_dir = WORKSPACE / "memory"
    cutoff_date = datetime.now() - timedelta(days=days)
    
    archived_count = 0
    skipped_count = 0
    freed_chars = 0
    
    if memory_dir.exists():
        for f in memory_dir.glob("*.md"):
            if f.name == "README.md":
                continue
            
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                content = f.read_text(encoding='utf-8')
                
                # 检查是否包含永久标记
                is_permanent = "📌" in content or "[P0]" in content
                
                if mtime < cutoff_date and not is_permanent:
                    size = f.stat().st_size
                    freed_chars += size
                    
                    if dry_run:
                        print(f"  📦 [模拟] {f.name} ({fmt_size(size)}, {file_age_days(f)} 天前)")
                    else:
                        # 移动到归档目录
                        archive_file = ARCHIVE_DIR / f"{datetime.now().strftime('%Y%m%d')}_{f.name}"
                        shutil.move(str(f), str(archive_file))
                        print(f"  📦 {f.name} → 归档 ({fmt_size(size)})")
                    
                    results["archived"].append(f.name)
                    archived_count += 1
                else:
                    if is_permanent:
                        print(f"  📌 跳过（永久）: {f.name}")
                    skipped_count += 1
                    results["skipped"].append(f.name)
            
            except Exception as e:
                print(f"  ⚠️ 归档失败: {f.name} - {str(e)}")
                results["errors"].append({"file": f.name, "error": str(e)})
    
    results["freed_tokens"] = freed_chars // 4
    
    # 总结
    print(f"\n{'='*50}")
    mode = "模拟" if dry_run else "实际"
    print(f"📦 {mode}归档完成:")
    print(f"   📄 归档文件: {archived_count}")
    print(f"   📌 跳过（永久）: {skipped_count}")
    print(f"   💾 节省: ~{fmt_tokens(results['freed_tokens'])} tokens")
    
    if not dry_run and archived_count > 0:
        print(f"   📁 归档位置: {ARCHIVE_DIR}")
    
    if getattr(args, 'json', False):
        print("\n\n--- JSON Output ---")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    return results


# ==================== 会话健康监控 ====================

def get_all_sessions():
    """获取所有会话的历史文件"""
    agents_dir = Path.home() / ".openclaw" / "agents"
    if not agents_dir.exists():
        return []
    
    sessions = []
    for agent_dir in agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        sessions_dir = agent_dir / "sessions"
        if not sessions_dir.exists():
            continue
        
        for f in sessions_dir.glob("*.jsonl"):
            if ".reset." in f.name or ".deleted." in f.name:
                continue
            try:
                size = f.stat().st_size
                with open(f, 'r', encoding='utf-8') as sf:
                    turns = sum(1 for line in sf if '"type":"message"' in line)
                sessions.append({
                    'agent': agent_dir.name,
                    'id': f.stem,
                    'path': f,
                    'size': size,
                    'tokens': size // 4,
                    'turns': turns,
                    'mtime': datetime.fromtimestamp(f.stat().st_mtime),
                })
            except Exception as e:
                # 会话文件可能正在写入，跳过并记录
                continue
    
    return sessions


def cmd_session(args):
    """会话检查命令"""
    results = {
        "sessions": [],
        "total_tokens": 0,
        "danger": [],
        "warn": [],
        "ok": []
    }
    
    sessions = get_all_sessions()
    if not sessions:
        if getattr(args, 'json', False):
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print("📭 未找到活跃会话")
        return results
    
    sessions.sort(key=lambda x: -x['tokens'])
    total_tokens = sum(s['tokens'] for s in sessions)
    results["total_tokens"] = total_tokens
    
    danger = [s for s in sessions if s['tokens'] > SESSION_DANGER_THRESHOLD]
    warn = [s for s in sessions if SESSION_WARN_THRESHOLD < s['tokens'] <= SESSION_DANGER_THRESHOLD]
    ok = [s for s in sessions if s['tokens'] <= SESSION_WARN_THRESHOLD]
    
    results["danger"] = [{'id': s['id'][:8], 'agent': s['agent'], 'tokens': s['tokens']} for s in danger]
    results["warn"] = [{'id': s['id'][:8], 'agent': s['agent'], 'tokens': s['tokens']} for s in warn]
    results["ok"] = len(ok)
    results["sessions"] = [{'id': s['id'][:8], 'agent': s['agent'], 'tokens': s['tokens']} for s in sessions]
    
    if getattr(args, 'json', False):
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return results
    
    print(f"🦞 龙虾医生 — 会话检查 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")
    print(f"📊 会话总览: {len(sessions)} 个活跃会话, ~{fmt_tokens(total_tokens)} tokens\n")
    
    if danger:
        print(f"🔴 危险会话 (>{fmt_tokens(SESSION_DANGER_THRESHOLD)} tokens): {len(danger)} 个")
        for s in danger[:5]:
            print(f"   🚨 {s['id']}... ({s['agent']}): ~{fmt_tokens(s['tokens'])} tokens")
        print()
    
    if warn:
        print(f"🟡 警告会话 (>{fmt_tokens(SESSION_WARN_THRESHOLD)} tokens): {len(warn)} 个")
        for s in warn[:5]:
            print(f"   ⚠️  {s['id']}... ({s['agent']}): ~{fmt_tokens(s['tokens'])} tokens")
        print()
    
    print(f"🟢 健康会话 (<{fmt_tokens(SESSION_WARN_THRESHOLD)} tokens): {len(ok)} 个\n")
    
    if danger or warn:
        print("💡 建议：")
        print("   /compress  — 压缩记忆")
        print("   /new       — 开新会话")
    
    return results


# ==================== 技能瘦身 ====================

def scan_skills():
    """扫描所有技能"""
    skills_dir = WORKSPACE / "skills"
    sys_skills_dir = Path.home() / ".npm-global" / "lib" / "node_modules" / "openclaw" / "skills"
    
    all_skills = []
    seen = set()
    
    for base_dir in [skills_dir, sys_skills_dir]:
        if not base_dir.exists():
            continue
        for skill_path in base_dir.iterdir():
            if not skill_path.is_dir() or skill_path.name in seen:
                continue
            seen.add(skill_path.name)
            
            skill_md = skill_path / "SKILL.md"
            if not skill_md.exists():
                continue
            
            try:
                content = skill_md.read_text(encoding='utf-8')
                fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
                if fm_match:
                    fm = fm_match.group(1)
                    desc_match = re.search(r'^description:\s*(.+?)(?=\n^[a-z]|\n---|\Z)', fm, re.MULTILINE | re.DOTALL)
                    if desc_match:
                        desc = desc_match.group(1)
                        desc = re.sub(r'^\s*>\s*', '', desc, flags=re.MULTILINE).strip()
                        tokens = estimate_tokens(desc)
                        all_skills.append({
                            'name': skill_path.name,
                            'path': skill_path,
                            'description': desc,
                            'tokens': tokens,
                        })
            except Exception:
                continue
    
    return all_skills


def cmd_slim(args):
    """技能瘦身命令"""
    results = {
        "skills": [],
        "total_tokens": 0,
        "suggestions": []
    }
    
    print(f"🦞 龙虾医生 — 技能瘦身 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")
    
    skills = scan_skills()
    if not skills:
        print("📭 未找到技能")
        return results
    
    skills.sort(key=lambda x: -x['tokens'])
    total_tokens = sum(s['tokens'] for s in skills)
    results["total_tokens"] = total_tokens
    results["skills"] = [{'name': s['name'], 'tokens': s['tokens']} for s in skills]
    
    print(f"📊 已安装技能: {len(skills)} 个, description 总量: ~{fmt_tokens(total_tokens)} tokens\n")
    
    # 找出 description 过长的技能
    long_skills = [s for s in skills if s['tokens'] > 50]
    
    if long_skills:
        print(f"📝 Description 较长的技能 (>{50} tokens):\n")
        for s in long_skills[:10]:
            print(f"   {s['name']}: ~{s['tokens']} tokens")
            # 简单建议：只保留第一句
            first_sentence = re.split(r'[。\n]', s['description'])[0]
            if len(first_sentence) < len(s['description']):
                suggested_tokens = estimate_tokens(first_sentence)
                saved = s['tokens'] - suggested_tokens
                results["suggestions"].append({
                    'name': s['name'],
                    'original_tokens': s['tokens'],
                    'suggested_tokens': suggested_tokens,
                    'saved_tokens': saved,
                })
                print(f"      💡 建议精简为: {first_sentence[:50]}...")
                print(f"      节省: ~{saved} tokens")
            print()
        
        if len(long_skills) > 10:
            print(f"   ... 还有 {len(long_skills) - 10} 个\n")
    
    # 总计
    if results["suggestions"]:
        total_saved = sum(s['saved_tokens'] for s in results["suggestions"])
        print(f"{'='*50}")
        print(f"💡 精简后可节省: ~{fmt_tokens(total_saved)} tokens/轮")
        print(f"\n   手动修改方法:")
        print(f"   1. 打开 skills/<技能名>/SKILL.md")
        print(f"   2. 找到 description 字段")
        print(f"   3. 精简为一句核心功能描述")
    
    if getattr(args, 'json', False):
        print("\n\n--- JSON Output ---")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    return results


# ==================== 安全清理 ====================

def cmd_cleanup(args):
    """安全清理命令"""
    dry_run = getattr(args, 'dry_run', False)
    
    if dry_run:
        print(f"🦞 龙虾医生 — 模拟清理 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")
    else:
        print(f"🦞 龙虾医生 — 安全清理 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")
    
    today = datetime.now().strftime('%Y-%m-%d')
    backup = BACKUP_DIR / f"backup-{today}"
    if not dry_run:
        backup.mkdir(parents=True, exist_ok=True)
    
    results = {
        "deleted_files": 0,
        "deleted_dirs": 0,
        "freed_bytes": 0,
        "backup_path": str(backup) if not dry_run else None
    }
    
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
                except Exception as e:
                    print(f"  ⚠️ 备份失败: {f.name} - {str(e)}")
                    continue
            results["deleted_files"] += 1
            results["freed_bytes"] += size
    
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
                except Exception as e:
                    print(f"  ⚠️ 备份失败: {rel} - {str(e)}")
                    continue
            results["deleted_files"] += 1
            results["freed_bytes"] += size
    
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
                results["deleted_dirs"] += 1
        except Exception as e:
            print(f"  ⚠️ 删除空目录失败: {d.name} - {str(e)}")
    
    # 4. 清理过期 memory 日志
    memory_dir = WORKSPACE / "memory"
    if memory_dir.exists():
        cutoff = datetime.now() - timedelta(days=MEMORY_LOG_MAX_DAYS)
        for f in memory_dir.glob('*.md'):
            if f.name == 'README.md':
                continue
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    size = f.stat().st_size
                    rel = f.relative_to(WORKSPACE)
                    if dry_run:
                        print(f"  📝 [模拟] 过期日志: {rel}")
                    else:
                        f.rename(backup / f.name)
                        print(f"  📝 过期日志已归档: {rel}")
                    results["deleted_files"] += 1
                    results["freed_bytes"] += size
            except Exception as e:
                print(f"  ⚠️ 处理日志失败: {f.name} - {str(e)}")
    
    # 总结
    print(f"\n{'='*50}")
    mode = "模拟" if dry_run else "实际"
    print(f"🧹 {mode}清理完成:")
    print(f"   📄 删除文件: {results['deleted_files']}")
    print(f"   📂 删除空目录: {results['deleted_dirs']}")
    print(f"   💾 释放空间: {fmt_size(results['freed_bytes'])}")
    if not dry_run and results["deleted_files"] > 0:
        print(f"   📦 备份位置: {backup}")
        print(f"\n💡 撤销命令: python3 scripts/lobster_doctor.py cleanup --undo")
    
    if getattr(args, 'json', False):
        print("\n\n--- JSON Output ---")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    return results


def cmd_cleanup_undo(args):
    """从备份恢复"""
    results = {"restored": [], "skipped": []}
    
    if not BACKUP_DIR.exists():
        print("❌ 没有找到备份目录")
        return results
    
    backups = sorted(BACKUP_DIR.glob("backup-*"), reverse=True)
    if not backups:
        print("❌ 没有找到备份")
        return results
    
    latest = backups[0]
    print(f"📦 从备份恢复: {latest.name}")
    
    for item in latest.iterdir():
        dest = WORKSPACE / item.name
        if dest.exists():
            print(f"  ⏭️ 跳过（已存在）: {item.name}")
            results["skipped"].append(item.name)
        else:
            try:
                shutil.copy2(item, dest)
                print(f"  ✅ 恢复: {item.name}")
                results["restored"].append(item.name)
            except Exception as e:
                print(f"  ❌ 失败: {item.name} - {e}")
                results["skipped"].append(item.name)
    
    print("✅ 恢复完成")
    
    if getattr(args, 'json', False):
        print("\n\n--- JSON Output ---")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    return results


# ==================== 健康检查 (Agent 主动) ====================

def cmd_health(args):
    """
    健康检查命令（Agent 定期执行）
    
    检测项：
    1. 会话状态（相对阈值）
    2. 废弃文件
    3. 技能描述大小
    4. Bootstrap context 大小
    5. 孤立进程检测
    6. 内存泄漏警告
    7. Token 计数器验证
    """
    results = {
        "issues": [],
        "sessions": {},
        "files": {},
        "skills": {},
        "bootstrap_tokens": 0,
        "orphan_processes": [],
        "memory_warnings": [],
        "token_anomalies": []
    }
    
    # 1. 会话检查（使用相对阈值）
    sessions = get_all_sessions()
    total_tokens = sum(s['tokens'] for s in sessions)
    
    # 计算相对阈值
    threshold_info = calculate_relative_threshold(total_tokens)
    
    # 使用相对阈值判断状态
    danger_sessions = []
    warn_sessions = []
    
    for s in sessions:
        s_threshold = calculate_relative_threshold(s['tokens'])
        if s_threshold['status'] == 'danger':
            danger_sessions.append(s)
        elif s_threshold['status'] == 'warning':
            warn_sessions.append(s)
    
    results["sessions"] = {
        "total": len(sessions),
        "total_tokens": total_tokens,
        "danger_count": len(danger_sessions),
        "warn_count": len(warn_sessions),
        "relative_threshold": threshold_info
    }
    
    if danger_sessions:
        results["issues"].append({
            "type": "danger_sessions",
            "count": len(danger_sessions),
            "details": [{'id': s['id'][:8], 'agent': s['agent'], 'tokens': s['tokens']} for s in danger_sessions[:5]]
        })
    
    if warn_sessions:
        results["issues"].append({
            "type": "warn_sessions",
            "count": len(warn_sessions)
        })
    
    # 2. 废弃文件检查
    stale_extensions = {'.py', '.js', '.html', '.txt', '.log'}
    stale_files = []
    for f in WORKSPACE.rglob('*'):
        if not f.is_file():
            continue
        if any(part in PROTECTED_DIRS for part in f.relative_to(WORKSPACE).parts):
            continue
        if f.suffix in stale_extensions:
            age = file_age_days(f)
            if age > STALE_DAYS_PY_JS_HTML:
                stale_files.append((f, age))
    
    results["files"] = {
        "stale_count": len(stale_files),
        "stale_size": sum(f.stat().st_size for f, _ in stale_files)
    }
    
    if len(stale_files) > 10:
        results["issues"].append({
            "type": "stale_files",
            "count": len(stale_files),
            "size": results["files"]["stale_size"]
        })
    
    # 3. 技能检查
    skills = scan_skills()
    total_desc_tokens = sum(s['tokens'] for s in skills)
    
    results["skills"] = {
        "total": len(skills),
        "desc_tokens": total_desc_tokens
    }
    
    if total_desc_tokens > 5000:
        results["issues"].append({
            "type": "skill_desc_large",
            "tokens": total_desc_tokens
        })
    
    # 4. Bootstrap context
    bootstrap_files = [WORKSPACE / name for name in CORE_FILES if (WORKSPACE / name).is_file()]
    bootstrap_chars = 0
    for f in bootstrap_files:
        try:
            bootstrap_chars += len(f.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"  ⚠️ 读取 Bootstrap 文件失败: {f.name} - {str(e)}")
    bootstrap_tokens = bootstrap_chars // 4
    results["bootstrap_tokens"] = bootstrap_tokens
    
    if bootstrap_tokens > 8000:
        results["issues"].append({
            "type": "bootstrap_large",
            "tokens": bootstrap_tokens
        })
    
    # 5. 孤立进程检测（新增）
    orphan_processes = detect_orphan_processes()
    results["orphan_processes"] = orphan_processes
    
    if orphan_processes:
        for orphan in orphan_processes:
            if orphan.get("type") != "error":
                results["issues"].append({
                    "type": "orphan_process",
                    "details": orphan
                })
    
    # 6. 内存泄漏警告（新增）
    memory_check = check_memory_leak()
    results["memory_warnings"] = memory_check.get("warnings", [])
    
    if memory_check.get("warnings"):
        for warning in memory_check["warnings"]:
            if warning.get("type") != "error":
                results["issues"].append({
                    "type": "memory_warning",
                    "details": warning
                })
    
    # 7. Token 计数器验证（新增）
    token_check = verify_token_counter()
    results["token_anomalies"] = token_check.get("anomalies", [])
    
    if token_check.get("status") != "ok":
        results["issues"].append({
            "type": "token_anomaly",
            "count": len(token_check.get("anomalies", []))
        })
    
    # 输出
    if getattr(args, 'json', False):
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(f"🦞 龙虾医生 — 健康检查 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")
        
        # 会话状态（相对阈值）
        status_icon = {"healthy": "🟢", "notice": "🔵", "warning": "🟡", "danger": "🔴"}
        status = status_icon.get(threshold_info['status'], "⚪")
        print(f"{status} 会话: {len(sessions)} 个, ~{fmt_tokens(total_tokens)} tokens ({threshold_info['percentage']}%)")
        print(f"   上下文窗口: {fmt_tokens(threshold_info['window'])} tokens")
        print(f"   剩余: ~{fmt_tokens(threshold_info['remaining'])} tokens")
        
        if danger_sessions:
            print(f"   🚨 危险会话: {len(danger_sessions)} 个")
        if warn_sessions:
            print(f"   ⚠️  警告会话: {len(warn_sessions)} 个")
        
        # 文件状态
        print(f"\n📦 废弃文件: {len(stale_files)} 个, {fmt_size(results['files']['stale_size'])}")
        
        # 技能状态
        print(f"\n🧩 技能: {len(skills)} 个, description ~{fmt_tokens(total_desc_tokens)} tokens")
        
        # Bootstrap
        print(f"\n🧠 Bootstrap: ~{fmt_tokens(bootstrap_tokens)} tokens")
        
        # 孤立进程
        if orphan_processes:
            print(f"\n👻 孤立进程: {len(orphan_processes)} 个")
            for p in orphan_processes[:3]:
                if p.get("type") != "error":
                    print(f"   • PID {p.get('pid', '?')}: {p.get('reason', '?')}")
        
        # 内存警告
        if memory_check.get("warnings"):
            print(f"\n💾 内存警告: {len(memory_check['warnings'])} 个")
            for w in memory_check["warnings"][:3]:
                print(f"   • {w.get('message', '?')}")
        
        # Token 异常
        if token_check.get("anomalies"):
            print(f"\n🔢 Token 异常: {len(token_check['anomalies'])} 个")
        
        # 问题汇总
        if results["issues"]:
            print(f"\n{'='*50}")
            print(f"⚠️ 发现 {len(results['issues'])} 个问题:")
            for issue in results["issues"]:
                if issue["type"] == "danger_sessions":
                    print(f"   🔴 危险会话: {issue['count']} 个")
                elif issue["type"] == "warn_sessions":
                    print(f"   🟡 警告会话: {issue['count']} 个")
                elif issue["type"] == "stale_files":
                    print(f"   📦 废弃文件: {issue['count']} 个, {fmt_size(issue['size'])}")
                elif issue["type"] == "skill_desc_large":
                    print(f"   🧩 技能描述过大: ~{fmt_tokens(issue['tokens'])} tokens")
                elif issue["type"] == "bootstrap_large":
                    print(f"   🧠 Bootstrap 过大: ~{fmt_tokens(issue['tokens'])} tokens")
                elif issue["type"] == "orphan_process":
                    print(f"   👻 孤立进程: {issue['details'].get('reason', '?')}")
                elif issue["type"] == "memory_warning":
                    print(f"   💾 内存警告: {issue['details'].get('message', '?')}")
                elif issue["type"] == "token_anomaly":
                    print(f"   🔢 Token 异常: {issue['count']} 个")
            
            print(f"\n💡 建议：")
            print(f"   python3 scripts/lobster_doctor.py slim     # 技能瘦身")
            print(f"   python3 scripts/lobster_doctor.py cleanup  # 安全清理")
            print(f"   python3 scripts/lobster_doctor.py archive  # Memory 归档")
        else:
            print(f"\n✅ 健康状况良好！")
    
    return results


# ==================== 主入口 ====================

def main():
    parser = argparse.ArgumentParser(description="🦞 Lobster Doctor v4.0 — 装得下，用得久，清得掉")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # archive (新增 P0)
    archive_parser = subparsers.add_parser("archive", help="Memory 归档（P0 核心）")
    archive_parser.add_argument("--dry-run", action="store_true", help="模拟运行")
    archive_parser.add_argument("--days", type=int, default=30, help="归档超过N天的记忆")
    archive_parser.add_argument("--undo", action="store_true", help="恢复最近归档")
    archive_parser.add_argument("--list", action="store_true", help="查看归档历史")
    archive_parser.add_argument("--json", action="store_true", help="JSON 输出")
    
    # slim
    slim_parser = subparsers.add_parser("slim", help="技能瘦身")
    slim_parser.add_argument("--json", action="store_true", help="JSON 输出")
    
    # cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="安全清理")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="模拟运行")
    cleanup_parser.add_argument("--undo", action="store_true", help="从备份恢复")
    cleanup_parser.add_argument("--json", action="store_true", help="JSON 输出")
    
    # session
    session_parser = subparsers.add_parser("session", help="会话检查（相对阈值）")
    session_parser.add_argument("--detail", action="store_true", help="详细分析")
    session_parser.add_argument("--predict", action="store_true", help="预测何时达到阈值")
    session_parser.add_argument("--json", action="store_true", help="JSON 输出")
    
    # health
    health_parser = subparsers.add_parser("health", help="健康检查（Agent 定期执行）")
    health_parser.add_argument("--json", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    if args.command is None:
        print("🦞 Lobster Doctor v4.0 — 装得下，用得久，清得掉\n")
        print("命令:")
        print("  archive           Memory 归档（P0 核心，延长会话续航）")
        print("  archive --days N  归档超过N天的记忆")
        print("  archive --undo    恢复最近归档")
        print("  slim              技能瘦身")
        print("  cleanup           安全清理")
        print("  cleanup --undo    撤销清理")
        print("  session           会话检查（相对阈值）")
        print("  health            健康检查（Agent 定期执行）")
        print()
        print("选项:")
        print("  --json            JSON 格式输出")
        print("  --dry-run         模拟运行")
        print()
        print("核心价值:")
        print("  装得下 — 技能瘦身，减少每轮注入量")
        print("  用得久 — 会话监控，相对阈值告警")
        print("  清得掉 — 安全清理，白名单保护")
        return
    
    if args.command == "archive":
        if getattr(args, 'undo', False):
            # 恢复归档（待实现）
            print("📦 恢复归档功能开发中...")
        elif getattr(args, 'list', False):
            # 查看归档历史（待实现）
            print("📋 归档历史功能开发中...")
        else:
            cmd_archive(args)
    elif args.command == "slim":
        cmd_slim(args)
    elif args.command == "cleanup":
        if getattr(args, 'undo', False):
            cmd_cleanup_undo(args)
        else:
            cmd_cleanup(args)
    elif args.command == "session":
        cmd_session(args)
    elif args.command == "health":
        cmd_health(args)


if __name__ == "__main__":
    main()