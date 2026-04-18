#!/usr/bin/env python3
"""
🦞 Lobster Doctor 全局配置

所有跨文件共享的常量定义在此处，禁止在其他模块中重复定义。

用法：
  from config import WORKSPACE, PROTECTED_DIRS, CORE_FILES, AI_TOOLS
"""

import os
from pathlib import Path

# ==================== 路径常量 ====================

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"

# ==================== 保护名单 ====================

# 受保护目录（不扫描不清理）
PROTECTED_DIRS = {"skills", "node_modules", ".git", "memory-tree", "memory"}

# 核心文件白名单（永不删除）
CORE_FILES = {
    "AGENTS.md", "SOUL.md", "USER.md", "MEMORY.md", "TOOLS.md",
    "HEARTBEAT.md", "IDENTITY.md", "PROGRESS.md", "INTEL-DIRECTIVE.md",
    "BOOTSTRAP.md", "KB-SYNC-GUIDE.md", "package.json", "package-lock.json",
    ".env", ".openclaw", ".git", ".gitignore",
    ".model_override", ".openclaw-model-override",
}

# ==================== AI 工具残留列表 ====================

AI_TOOLS = [
    ".windsurf", ".continue", ".crush", ".goose", ".kiro", ".kilocode",
    ".roo", ".qoder", ".trae", ".vibe", ".zencoder", ".openhands",
    ".pi", ".pochi", ".mux", ".neovate", ".mcpjam", ".junie", ".iflow",
    ".factory", ".cortex", ".commandcode", ".codebuddy", ".augment", ".adal",
    ".kode", ".qwen",
]
