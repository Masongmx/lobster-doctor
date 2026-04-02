#!/usr/bin/env python3
"""
🦞 Lobster Doctor TUI Panels Component

三面板布局组件：
  - SessionsPanel: 显示会话 token 占用进度条
  - FilesPanel: 显示废弃文件统计
  - SkillsPanel: 显示技能 description token 统计

功能：
  - 面板可滚动（继承 ScrollableContainer）
  - 颜色标记（🟢🟡🔴）
  - 数据绑定（调用 tui_data 函数）
  - 进度条动画
"""

from textual.widget import Widget
from textual.containers import ScrollableContainer, Horizontal
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from rich.style import Style

from tui_data import (
    get_summary, get_hidden_folders, get_large_files, 
    get_violations, get_health_status, _fmt_size
)


class BasePanel(ScrollableContainer):
    """
    面板基类

    提供通用的数据刷新和渲染逻辑。
    """

    # 刷新间隔（秒）
    REFRESH_INTERVAL = 5
    PANEL_TITLE = "Panel"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._refresh_timer = None

    def on_mount(self) -> None:
        """组件挂载时初始化"""
        self._refresh_data()
        self._refresh_timer = self.set_interval(self.REFRESH_INTERVAL, self._refresh_data)

    def on_unmount(self) -> None:
        """组件卸载时清理"""
        if self._refresh_timer:
            self._refresh_timer.stop()

    def _refresh_data(self) -> None:
        """刷新数据 - 子类实现"""
        pass

    def _get_color_for_percentage(self, percentage: float) -> str:
        """根据百分比获取颜色"""
        if percentage < 50:
            return "green"
        elif percentage < 80:
            return "yellow"
        else:
            return "red"

    def _get_status_icon(self, value: int, thresholds: tuple = (50, 80)) -> str:
        """根据值获取状态图标"""
        if value < thresholds[0]:
            return "🟢"
        elif value < thresholds[1]:
            return "🟡"
        else:
            return "🔴"


class SessionsPanel(BasePanel):
    """
    会话面板

    显示会话 token 占用进度条。
    """

    PANEL_TITLE = "📊 Sessions"

    # 响应式数据
    total_sessions = reactive(0, layout=True)
    active_sessions = reactive(0, layout=True)
    total_tokens = reactive(0, layout=True)
    max_tokens = reactive(1000000, layout=True)  # 1M tokens 默认上限
    token_percentage = reactive(0.0, layout=True)
    sessions_data = reactive([], layout=True)

    def _refresh_data(self) -> None:
        """刷新会话数据"""
        try:
            # 从 tui_data 获取数据（模拟）
            # 实际应该从 session 管理器获取
            summary = get_summary()

            # 模拟会话数据
            # TODO: 集成真实 session 管理器
            self.total_sessions = 3
            self.active_sessions = 2
            self.total_tokens = 250000
            self.max_tokens = 1000000
            self.token_percentage = (self.total_tokens / self.max_tokens) * 100

        except Exception as e:
            self.total_sessions = 0
            self.active_sessions = 0
            self.total_tokens = 0
            self.token_percentage = 0.0

    def render(self) -> Text:
        """渲染会话面板"""
        text = Text()

        # 标题
        text.append(self.PANEL_TITLE, style=Style(bold=True, color="cyan"))
        text.append("\n\n")

        # 会话统计
        text.append("Total Sessions: ", style=Style(color="white"))
        text.append(str(self.total_sessions), style=Style(bold=True))
        text.append("\n")

        text.append("Active Sessions: ", style=Style(color="white"))
        text.append(str(self.active_sessions), style=Style(color="green", bold=True))
        text.append("\n\n")

        # Token 使用进度条
        text.append("Token Usage: ", style=Style(color="white"))
        color = self._get_color_for_percentage(self.token_percentage)
        text.append(f"{self.total_tokens:,}", style=Style(color=color, bold=True))
        text.append(f" / {self.max_tokens:,}")
        text.append(f" ({self.token_percentage:.1f}%)", style=Style(color=color))
        text.append("\n")

        # 文本进度条
        bar_width = 20
        filled = int(self.token_percentage / 100 * bar_width)
        empty = bar_width - filled
        bar = "█" * filled + "░" * empty
        text.append(f"  [{bar}] ", style=Style(color=color))

        # 状态图标
        if self.token_percentage < 50:
            icon = "🟢"
        elif self.token_percentage < 80:
            icon = "🟡"
        else:
            icon = "🔴"
        text.append(icon)

        return text


class FilesPanel(BasePanel):
    """
    文件面板

    显示废弃文件和大文件统计。
    """

    PANEL_TITLE = "📁 Files"

    # 响应式数据
    hidden_folders_count = reactive(0, layout=True)
    large_files_count = reactive(0, layout=True)
    violations_count = reactive(0, layout=True)
    total_waste_size = reactive(0, layout=True)
    files_data = reactive([], layout=True)

    def _refresh_data(self) -> None:
        """刷新文件数据"""
        try:
            summary = get_summary()
            hidden = get_hidden_folders()
            large = get_large_files()
            violations = get_violations()

            self.hidden_folders_count = len(hidden)
            self.large_files_count = len(large)
            self.violations_count = len(violations)

            # 计算总浪费空间
            waste_size = sum(f.get("size", 0) for f in large)
            self.total_waste_size = waste_size

            self.files_data = {
                "hidden": hidden,
                "large": large,
                "violations": violations
            }

        except Exception as e:
            self.hidden_folders_count = 0
            self.large_files_count = 0
            self.violations_count = 0
            self.total_waste_size = 0

    def render(self) -> Text:
        """渲染文件面板"""
        text = Text()

        # 标题
        text.append(self.PANEL_TITLE, style=Style(bold=True, color="cyan"))
        text.append("\n\n")

        # 隐藏文件夹
        text.append("Hidden Folders: ", style=Style(color="white"))
        hidden_color = "green" if self.hidden_folders_count <= 3 else ("yellow" if self.hidden_folders_count <= 5 else "red")
        text.append(str(self.hidden_folders_count), style=Style(color=hidden_color, bold=True))
        text.append(f" {self._get_status_icon(self.hidden_folders_count, (4, 6))}")
        text.append("\n")

        # 大文件
        text.append("Large Files: ", style=Style(color="white"))
        large_color = "green" if self.large_files_count == 0 else ("yellow" if self.large_files_count <= 3 else "red")
        text.append(str(self.large_files_count), style=Style(color=large_color, bold=True))
        text.append(f" {self._get_status_icon(self.large_files_count * 20, (30, 60))}")
        text.append("\n")

        # 违规项
        text.append("Violations: ", style=Style(color="white"))
        violations_color = "green" if self.violations_count == 0 else ("yellow" if self.violations_count <= 2 else "red")
        text.append(str(self.violations_count), style=Style(color=violations_color, bold=True))
        text.append(f" {self._get_status_icon(self.violations_count * 30, (30, 60))}")
        text.append("\n\n")

        # 总浪费空间
        text.append("Total Waste: ", style=Style(color="white"))
        waste_color = "green" if self.total_waste_size < 50 * 1024 * 1024 else ("yellow" if self.total_waste_size < 100 * 1024 * 1024 else "red")
        text.append(_fmt_size(self.total_waste_size), style=Style(color=waste_color, bold=True))

        return text


class SkillsPanel(BasePanel):
    """
    技能面板

    显示技能 description token 统计。
    """

    PANEL_TITLE = "🎯 Skills"

    # 响应式数据
    total_skills = reactive(0, layout=True)
    total_desc_tokens = reactive(0, layout=True)
    avg_tokens = reactive(0, layout=True)
    max_tokens_skill = reactive("", layout=True)
    skills_data = reactive([], layout=True)

    def _refresh_data(self) -> None:
        """刷新技能数据"""
        try:
            # 模拟技能数据
            # TODO: 从 skills 目录读取真实数据
            self.total_skills = 47
            self.total_desc_tokens = 150000
            self.avg_tokens = int(self.total_desc_tokens / max(self.total_skills, 1))
            self.max_tokens_skill = "deep-research-pro"

        except Exception as e:
            self.total_skills = 0
            self.total_desc_tokens = 0
            self.avg_tokens = 0
            self.max_tokens_skill = ""

    def render(self) -> Text:
        """渲染技能面板"""
        text = Text()

        # 标题
        text.append(self.PANEL_TITLE, style=Style(bold=True, color="cyan"))
        text.append("\n\n")

        # 总技能数
        text.append("Total Skills: ", style=Style(color="white"))
        text.append(str(self.total_skills), style=Style(bold=True, color="cyan"))
        text.append("\n")

        # Description tokens
        text.append("Desc Tokens: ", style=Style(color="white"))
        token_color = self._get_color_for_percentage(self.total_desc_tokens / 200000 * 100)
        text.append(f"{self.total_desc_tokens:,}", style=Style(color=token_color, bold=True))
        text.append("\n")

        # 平均 tokens
        text.append("Avg Tokens: ", style=Style(color="white"))
        text.append(f"{self.avg_tokens:,}", style=Style(bold=True))
        text.append("\n\n")

        # 最大 tokens 技能
        text.append("Largest: ", style=Style(color="white"))
        if self.max_tokens_skill:
            text.append(self.max_tokens_skill, style=Style(color="yellow", bold=True))
        else:
            text.append("N/A", style=Style(color="dim"))

        return text


class PanelsContainer(Horizontal):
    """
    三面板容器

    将三个面板并排显示。
    """

    CSS = """
    PanelsContainer {
        height: auto;
        min-height: 12;
        padding: 1;
    }

    PanelsContainer > BasePanel {
        width: 1fr;
        height: auto;
        min-height: 10;
        border: solid $primary;
        padding: 1;
        margin: 0 1;
    }
    """

    def compose(self):
        """构建三面板布局"""
        yield SessionsPanel(classes="panel")
        yield FilesPanel(classes="panel")
        yield SkillsPanel(classes="panel")


# 便于导入
__all__ = [
    "BasePanel",
    "SessionsPanel", 
    "FilesPanel",
    "SkillsPanel",
    "PanelsContainer"
]


if __name__ == "__main__":
    # 简单测试
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer

    class TestApp(App):
        CSS = """
        Screen {
            layout: vertical;
        }

        BasePanel {
            width: 1fr;
            height: auto;
            min-height: 10;
            border: solid cyan;
            padding: 1;
            margin: 1;
        }

        Horizontal {
            height: auto;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with Horizontal():
                yield SessionsPanel()
                yield FilesPanel()
                yield SkillsPanel()
            yield Footer()

    app = TestApp()
    app.run()
