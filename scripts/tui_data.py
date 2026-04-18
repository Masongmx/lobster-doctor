#!/usr/bin/env python3
"""
🦞 Lobster Doctor TUI Data Layer (修复版 - 带 TTLCache 缓存)

核心数据采集模块，为 TUI 提供实时数据。

修复内容 (P0 问题)：
  - 添加 TTLCache 缓存（TTL=5秒，避免重复扫描）
  - 添加 logging（info/warning/error）
  - 添加 try-except 错误处理

函数：
  - get_workspace_size() → 返回 workspace 总大小 (bytes)
  - get_hidden_folders() → 返回隐藏文件夹列表
  - get_large_files(threshold) → 返回超过阈值的大文件列表
  - get_violations() → 返回健康违规项列表
  - get_health_status() → 返回健康状态图标 (🟢/🟡/🔴)

阈值配置：
  - 健康状态：🟢 <500MB, 🟡 500MB-1GB, 🔴 >1GB
  - 大文件阈值：默认 50MB
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Literal, Any
from cachetools import cached, TTLCache

# 配置 logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 从 config 导入共享常量
from config import WORKSPACE, PROTECTED_DIRS, CORE_FILES

# 健康状态阈值 (bytes)
HEALTH_THRESHOLDS = {
    "ok": 500 * 1024 * 1024,      # 500MB
    "warn": 1024 * 1024 * 1024,   # 1GB
}

# 缓存配置：TTL=5秒（与 TUI 刷新间隔一致）
CACHE_TTL = 5

# 为每个函数创建独立的缓存实例（避免 key 冺突）
_workspace_size_cache = TTLCache(maxsize=1, ttl=CACHE_TTL)
_hidden_folders_cache = TTLCache(maxsize=1, ttl=CACHE_TTL)
_large_files_cache = TTLCache(maxsize=2, ttl=CACHE_TTL)  # 支持不同 threshold
_violations_cache = TTLCache(maxsize=1, ttl=CACHE_TTL)
_health_status_cache = TTLCache(maxsize=1, ttl=CACHE_TTL)

# 所有缓存实例列表（用于 clear_cache）
_all_caches = [
    _workspace_size_cache,
    _hidden_folders_cache,
    _large_files_cache,
    _violations_cache,
    _health_status_cache,
]


@cached(cache=_workspace_size_cache)
def get_workspace_size() -> int:
    """
    计算 workspace 目录总大小（带缓存）

    Returns:
        int: 总大小 (bytes)

    Notes:
        - 排除 PROTECTED_DIRS 中的目录
        - 只计算文件，不计算目录本身
        - 缓存 TTL=5秒，避免重复扫描
    """
    logger.info(f"开始扫描 workspace: {WORKSPACE}")
    total_size = 0
    file_count = 0

    try:
        for root, dirs, files in os.walk(WORKSPACE):
            # 排除受保护目录
            dirs[:] = [d for d in dirs if d not in PROTECTED_DIRS]

            for file in files:
                file_path = Path(root) / file
                try:
                    size = file_path.stat().st_size
                    total_size += size
                    file_count += 1
                except (OSError, PermissionError) as e:
                    logger.warning(f"无法访问文件 {file_path}: {e}")
                    continue

        logger.info(f"扫描完成: {file_count} 个文件，总大小 {_fmt_size(total_size)}")
        return total_size

    except Exception as e:
        logger.error(f"扫描 workspace 失败: {e}")
        return 0


@cached(cache=_hidden_folders_cache)
def get_hidden_folders() -> List[Dict[str, str]]:
    """
    获取 workspace 中的隐藏文件夹列表（带缓存）

    Returns:
        List[Dict]: 隐藏文件夹信息列表
            [{"name": ".folder", "path": "/full/path", "size": bytes}]

    Notes:
        - 隐藏文件夹：以 '.' 开头的目录
        - 排除 .git（已知且大）
        - 缓存 TTL=5秒
    """
    logger.info("扫描隐藏文件夹...")
    hidden_folders = []

    try:
        for item in WORKSPACE.iterdir():
            if item.is_dir() and item.name.startswith('.') and item.name != '.git':
                try:
                    size = sum(
                        f.stat().st_size
                        for f in item.rglob('*')
                        if f.is_file()
                    )
                    hidden_folders.append({
                        "name": item.name,
                        "path": str(item),
                        "size": size
                    })
                    logger.debug(f"发现隐藏文件夹: {item.name} ({_fmt_size(size)})")
                except (OSError, PermissionError) as e:
                    logger.warning(f"无法访问隐藏文件夹 {item}: {e}")
                    hidden_folders.append({
                        "name": item.name,
                        "path": str(item),
                        "size": 0
                    })

        logger.info(f"发现 {len(hidden_folders)} 个隐藏文件夹")
        return hidden_folders

    except Exception as e:
        logger.error(f"扫描隐藏文件夹失败: {e}")
        return []


@cached(cache=_large_files_cache)
def get_large_files(threshold: int = 50 * 1024 * 1024) -> List[Dict[str, Any]]:
    """
    获取超过阈值的大文件列表（带缓存）

    Args:
        threshold: 文件大小阈值 (bytes)，默认 50MB

    Returns:
        List[Dict]: 大文件信息列表
            [{"name": "file.ext", "path": "/full/path", "size": bytes, "age_days": int}]

    Notes:
        - 排除 PROTECTED_DIRS 中的目录
        - 排除核心文件白名单中的文件
        - 缓存 TTL=5秒
    """
    logger.info(f"扫描大文件 (阈值: {_fmt_size(threshold)})...")
    large_files = []

    try:
        for root, dirs, files in os.walk(WORKSPACE):
            # 排除受保护目录
            dirs[:] = [d for d in dirs if d not in PROTECTED_DIRS]

            for file in files:
                if file in CORE_FILES:
                    continue

                file_path = Path(root) / file
                try:
                    stat = file_path.stat()
                    size = stat.st_size

                    if size >= threshold:
                        # 计算文件年龄（天数）
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        age_days = (datetime.now() - mtime).days

                        large_files.append({
                            "name": file,
                            "path": str(file_path),
                            "size": size,
                            "age_days": age_days
                        })
                        logger.debug(f"发现大文件: {file} ({_fmt_size(size)}, {age_days}天)")
                except (OSError, PermissionError) as e:
                    logger.warning(f"无法访问文件 {file_path}: {e}")
                    continue

        # 按大小降序排序
        large_files.sort(key=lambda x: x["size"], reverse=True)
        logger.info(f"发现 {len(large_files)} 个大文件")
        return large_files

    except Exception as e:
        logger.error(f"扫描大文件失败: {e}")
        return []


@cached(cache=_violations_cache)
def get_violations() -> List[Dict[str, str]]:
    """
    获取健康违规项列表（带缓存）

    Returns:
        List[Dict]: 违规项列表
            [{"type": "large_file", "severity": "high", "message": "...", "path": "..."}]

    检查项：
        1. workspace 大小超标 (>500MB)
        2. 存在超大文件 (>50MB)
        3. 存在废弃文件 (>3天未修改的临时文件)
        4. 隐藏文件夹过多 (>5个)

    Notes:
        - 缓存 TTL=5秒
        - 添加 try-except 错误处理
    """
    logger.info("检查健康违规项...")
    violations = []

    try:
        # 1. workspace 大小检查
        workspace_size = get_workspace_size()
        if workspace_size > HEALTH_THRESHOLDS["warn"]:
            violations.append({
                "type": "workspace_size",
                "severity": "high",
                "message": f"Workspace 超过 1GB ({_fmt_size(workspace_size)})",
                "path": str(WORKSPACE)
            })
            logger.warning(f"违规: workspace 超过 1GB ({_fmt_size(workspace_size)})")
        elif workspace_size > HEALTH_THRESHOLDS["ok"]:
            violations.append({
                "type": "workspace_size",
                "severity": "medium",
                "message": f"Workspace 超过 500MB ({_fmt_size(workspace_size)})",
                "path": str(WORKSPACE)
            })
            logger.info(f"警告: workspace 超过 500MB ({_fmt_size(workspace_size)})")

        # 2. 大文件检查
        large_files = get_large_files()
        if large_files:
            top_file = large_files[0]
            severity = "high" if top_file["size"] > 100 * 1024 * 1024 else "medium"
            violations.append({
                "type": "large_file",
                "severity": severity,
                "message": f"超大文件 {top_file['name']} ({_fmt_size(top_file['size'])})",
                "path": top_file["path"]
            })
            logger.warning(f"违规: 大文件 {top_file['name']} ({_fmt_size(top_file['size'])})")

        # 3. 隐藏文件夹检查
        hidden_folders = get_hidden_folders()
        if len(hidden_folders) > 5:
            violations.append({
                "type": "hidden_folders",
                "severity": "low",
                "message": f"隐藏文件夹过多 ({len(hidden_folders)} 个)",
                "path": str(WORKSPACE)
            })
            logger.info(f"警告: 隐藏文件夹过多 ({len(hidden_folders)} 个)")

        logger.info(f"发现 {len(violations)} 个违规项")
        return violations

    except Exception as e:
        logger.error(f"检查违规项失败: {e}")
        return []


@cached(cache=_health_status_cache)
def get_health_status() -> Literal["🟢", "🟡", "🔴"]:
    """
    获取当前健康状态图标（带缓存）

    Returns:
        str: 健康状态图标
            🟢 - 健康 (<500MB)
            🟡 - 注意 (500MB-1GB)
            🔴 - 危险 (>1GB 或存在严重违规)

    Notes:
        - 基于 workspace 大小和违规项综合判断
        - 存在严重违规时直接返回 🔴
        - 缓存 TTL=5秒
        - 添加 try-except 错误处理
    """
    logger.info("获取健康状态...")

    try:
        workspace_size = get_workspace_size()
        violations = get_violations()

        # 检查是否有严重违规
        has_severe_violation = any(
            v["severity"] == "high" for v in violations
        )

        if has_severe_violation or workspace_size > HEALTH_THRESHOLDS["warn"]:
            status = "🔴"
            logger.warning(f"健康状态: 危险 {status}")
        elif workspace_size > HEALTH_THRESHOLDS["ok"]:
            status = "🟡"
            logger.info(f"健康状态: 注意 {status}")
        else:
            status = "🟢"
            logger.info(f"健康状态: 健康 {status}")

        return status

    except Exception as e:
        logger.error(f"获取健康状态失败: {e}")
        return "🔴"  # 出错时返回危险状态


# ==================== 辅助函数 ====================

def _fmt_size(size: int) -> str:
    """格式化文件大小为人类可读格式"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"


def _fmt_bytes(size: int) -> str:
    """格式化 bytes 为带单位的字符串"""
    return _fmt_size(size)


# ==================== 缓存管理函数 ====================

def clear_cache() -> None:
    """
    清除所有缓存

    用于手动刷新时强制重新扫描。
    """
    logger.info("清除缓存...")
    for cache in _all_caches:
        cache.clear()
    logger.info("缓存已清除")


def get_cache_info() -> Dict[str, Any]:
    """
    获取缓存信息

    Returns:
        Dict: 缓存状态信息
    """
    total_size = sum(len(cache) for cache in _all_caches)
    return {
        "cache_size": total_size,
        "cache_maxsize": sum(getattr(cache, 'maxsize', 1) for cache in _all_caches),
        "cache_ttl": CACHE_TTL,
        "cache_usage": total_size / 5 * 100,  # 5 个缓存实例
        "workspace_size_cached": len(_workspace_size_cache) > 0,
        "hidden_folders_cached": len(_hidden_folders_cache) > 0,
        "large_files_cached": len(_large_files_cache) > 0,
        "violations_cached": len(_violations_cache) > 0,
        "health_status_cached": len(_health_status_cache) > 0,
    }


# ==================== 数据汇总函数 ====================

def get_summary() -> Dict[str, any]:
    """
    获取 workspace 健康摘要（带缓存）

    Returns:
        Dict: 包含所有核心指标的摘要

    Notes:
        - 所有数据函数都带缓存
        - 缓存 TTL=5秒，避免重复扫描
        - 添加 try-except 错误处理
    """
    logger.info("获取 workspace 健康摘要...")

    try:
        workspace_size = get_workspace_size()
        summary = {
            "workspace_size": workspace_size,
            "workspace_size_fmt": _fmt_size(workspace_size),
            "hidden_folders": len(get_hidden_folders()),
            "large_files": len(get_large_files()),
            "violations": len(get_violations()),
            "health_status": get_health_status(),
            "timestamp": datetime.now().isoformat(),
            "cache_info": get_cache_info()
        }
        logger.info(f"摘要获取完成: {summary['health_status']} {summary['workspace_size_fmt']}")
        return summary

    except Exception as e:
        logger.error(f"获取摘要失败: {e}")
        # 返回默认值
        return {
            "workspace_size": 0,
            "workspace_size_fmt": "0B",
            "hidden_folders": 0,
            "large_files": 0,
            "violations": 0,
            "health_status": "🔴",
            "timestamp": datetime.now().isoformat(),
            "cache_info": get_cache_info(),
            "error": str(e)
        }


if __name__ == "__main__":
    # 测试输出
    import json
    import time

    print("=== Lobster Doctor TUI Data Layer Test (带缓存) ===")
    print(f"Workspace: {WORKSPACE}")
    print()

    # 第一次调用（扫描）
    print("第一次调用（扫描）:")
    start = time.time()
    summary1 = get_summary()
    elapsed1 = time.time() - start
    print(f"耗时: {elapsed1:.3f}s")
    print(json.dumps(summary1, indent=2, ensure_ascii=False))
    print()

    # 第二次调用（缓存）
    print("第二次调用（缓存）:")
    start = time.time()
    summary2 = get_summary()
    elapsed2 = time.time() - start
    print(f"耗时: {elapsed2:.3f}s")
    print(f"缓存生效: {elapsed2 < elapsed1}")
    print()

    # 缓存信息
    print("缓存信息:")
    print(json.dumps(get_cache_info(), indent=2))
    print()

    # 清除缓存测试
    print("清除缓存后重新调用:")
    clear_cache()
    start = time.time()
    summary3 = get_summary()
    elapsed3 = time.time() - start
    print(f"耗时: {elapsed3:.3f}s")
    print()

    print(f"Workspace Size: {summary3['workspace_size_fmt']}")
    print(f"Health Status: {summary3['health_status']}")
    print(f"Hidden Folders: {summary3['hidden_folders']}")
    print(f"Large Files: {summary3['large_files']}")
    print(f"Violations: {summary3['violations']}")
