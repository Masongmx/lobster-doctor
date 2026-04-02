#!/usr/bin/env python3
"""
🦞 Lobster Doctor TUI Components Tests

测试 Header 和 Panel 组件功能。

测试范围：
  - Header 渲染正常
  - 颜色根据阈值变化（<500MB🟢, 500MB-1GB🟡, >1GB🔴）
  - 刷新间隔 5 秒
  - 内存占用 <10MB
  - 三面板并排显示
  - 进度条动画流畅
  - 滚动正常
  - 数据实时更新
"""

import pytest
import sys
import os
import time
import tracemalloc
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# ==================== Header 组件测试 ====================

class TestHeaderWidget:
    """Header 组件测试"""

    def test_header_render(self):
        """测试 Header 渲染正常"""
        from tui_header import HeaderWidget

        header = HeaderWidget()

        # 直接设置 reactive 属性测试渲染逻辑
        header.workspace_size = "300.0MB"
        header.workspace_size_bytes = 300 * 1024 * 1024
        header.hidden_folders = 2
        header.health_status = "🟢"

        # 验证 render 方法能正常工作
        render_result = header.render()
        assert render_result is not None

        # 验证数据已设置
        assert header.workspace_size == "300.0MB"
        assert header.hidden_folders == 2
        assert header.health_status == "🟢"

    def test_header_color_threshold_green(self):
        """测试颜色阈值 - 绿色 (<500MB)"""
        from tui_header import HeaderWidget

        header = HeaderWidget()
        header.workspace_size_bytes = 400 * 1024 * 1024  # 400MB

        color = header._get_size_color()
        assert color == "green"

    def test_header_color_threshold_yellow(self):
        """测试颜色阈值 - 黄色 (500MB-1GB)"""
        from tui_header import HeaderWidget

        header = HeaderWidget()
        header.workspace_size_bytes = 700 * 1024 * 1024  # 700MB

        color = header._get_size_color()
        assert color == "yellow"

    def test_header_color_threshold_red(self):
        """测试颜色阈值 - 红色 (>1GB)"""
        from tui_header import HeaderWidget

        header = HeaderWidget()
        header.workspace_size_bytes = 1500 * 1024 * 1024  # 1.5GB

        color = header._get_size_color()
        assert color == "red"

    def test_header_refresh_interval(self):
        """测试刷新间隔为 5 秒"""
        from tui_header import HeaderWidget

        header = HeaderWidget()
        assert header.REFRESH_INTERVAL == 5

    def test_header_memory_usage(self):
        """测试内存占用 <10MB"""
        tracemalloc.start()

        from tui_header import HeaderWidget

        # 创建多个 Header 实例
        headers = [HeaderWidget() for _ in range(10)]

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # 10 个实例峰值应 <10MB
        assert peak < 10 * 1024 * 1024, f"Memory peak {peak / 1024 / 1024:.1f}MB exceeds 10MB"


# ==================== Panel 组件测试 ====================

class TestSessionsPanel:
    """Sessions 面板测试"""

    def test_sessions_panel_render(self):
        """测试 Sessions 面板渲染"""
        from tui_panels import SessionsPanel

        panel = SessionsPanel()
        panel._refresh_data()

        # 验证数据已设置
        assert panel.total_sessions >= 0
        assert panel.active_sessions >= 0
        assert panel.total_tokens >= 0
        assert panel.token_percentage >= 0

    def test_sessions_progress_bar_logic(self):
        """测试进度条逻辑"""
        from tui_panels import SessionsPanel

        panel = SessionsPanel()

        # 测试百分比颜色逻辑
        assert panel._get_color_for_percentage(30) == "green"
        assert panel._get_color_for_percentage(60) == "yellow"
        assert panel._get_color_for_percentage(90) == "red"


class TestFilesPanel:
    """Files 面板测试"""

    def test_files_panel_render(self):
        """测试 Files 面板渲染"""
        from tui_panels import FilesPanel

        panel = FilesPanel()
        panel._refresh_data()

        # 验证数据已设置
        assert panel.hidden_folders_count >= 0
        assert panel.large_files_count >= 0
        assert panel.violations_count >= 0

    def test_files_panel_status_icon(self):
        """测试状态图标逻辑"""
        from tui_panels import FilesPanel

        panel = FilesPanel()

        # 测试阈值
        assert panel._get_status_icon(20, (50, 80)) == "🟢"
        assert panel._get_status_icon(60, (50, 80)) == "🟡"
        assert panel._get_status_icon(90, (50, 80)) == "🔴"


class TestSkillsPanel:
    """Skills 面板测试"""

    def test_skills_panel_render(self):
        """测试 Skills 面板渲染"""
        from tui_panels import SkillsPanel

        panel = SkillsPanel()
        panel._refresh_data()

        # 验证数据已设置
        assert panel.total_skills >= 0
        assert panel.total_desc_tokens >= 0
        assert panel.avg_tokens >= 0


class TestPanelsIntegration:
    """面板集成测试"""

    def test_three_panels_side_by_side(self):
        """测试三面板并排显示"""
        from tui_panels import SessionsPanel, FilesPanel, SkillsPanel, PanelsContainer

        # 创建容器
        container = PanelsContainer()

        # 验证容器包含三个面板
        # compose 方法返回生成器，需要实例化验证
        panels = list(container.compose())
        assert len(panels) == 3
        assert isinstance(panels[0], SessionsPanel)
        assert isinstance(panels[1], FilesPanel)
        assert isinstance(panels[2], SkillsPanel)

    def test_panels_scrollable(self):
        """测试面板可滚动"""
        from tui_panels import BasePanel, SessionsPanel

        # 验证继承自 ScrollableContainer
        assert issubclass(SessionsPanel, BasePanel)

        panel = SessionsPanel()
        # ScrollableContainer 继承链
        assert hasattr(panel, 'scroll_to')

    def test_panels_refresh_interval(self):
        """测试面板刷新间隔"""
        from tui_panels import SessionsPanel, FilesPanel, SkillsPanel

        # 所有面板刷新间隔应为 5 秒
        for panel_class in [SessionsPanel, FilesPanel, SkillsPanel]:
            assert panel_class.REFRESH_INTERVAL == 5


# ==================== TUI 集成测试 ====================

class TestLobsterDoctorApp:
    """LobsterDoctorApp 集成测试"""

    def test_app_compose(self):
        """测试 App compose 方法"""
        from lobster_tui import LobsterDoctorApp

        app = LobsterDoctorApp()

        # 验证 compose 方法存在
        assert hasattr(app, 'compose')

        # 验证 BINDINGS 和 CSS 定义正确
        assert app.CSS is not None
        assert len(app.BINDINGS) >= 6

    def test_app_bindings(self):
        """测试快捷键绑定"""
        from lobster_tui import LobsterDoctorApp

        app = LobsterDoctorApp()

        # 验证 BINDINGS 包含所有快捷键
        binding_keys = [b.key for b in app.BINDINGS]
        assert 'a' in binding_keys  # Archive
        assert 's' in binding_keys  # Slim
        assert 'c' in binding_keys  # Cleanup
        assert 'h' in binding_keys  # Health
        assert 'r' in binding_keys  # Refresh
        assert 'q' in binding_keys  # Quit

    def test_app_title(self):
        """测试 App 标题"""
        from lobster_tui import LobsterDoctorApp

        app = LobsterDoctorApp()
        assert "Lobster Doctor" in app.TITLE


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
