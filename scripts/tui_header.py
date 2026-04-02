#!/usr/bin/env python3
"""
🦞 Lobster Doctor TUI Header Component

Header 组件：显示 workspace 健康状态摘要。

功能：
  - 显示 workspace 大小（带颜色标记 🟢🟡🔴）
  - 显示隐藏文件夹数量
  - 显示健康状态图标
  - 5 秒自动刷新
  - 数据绑定到 tui_data.get_summary()

颜色阈值：
  - 🟢 健康: <500MB
  - 🟡 注意: 500MB-1GB
  - 🔴 危险: >1GB
"""

from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from rich.style import Style

from tui_data import get_summary, get_health_status


class HeaderWidget(Widget):
    """
    自定义 Header 组件

    显示 workspace 健康状态摘要，每 5 秒自动刷新。
    """

    # 响应式数据
    workspace_size = reactive("", layout=True)
    workspace_size_bytes = reactive(0, layout=False)
    hidden_folders = reactive(0, layout=True)
    health_status = reactive("🟢", layout=True)
    last_update = reactive("", layout=True)

    # 刷新间隔（秒）
    REFRESH_INTERVAL = 5

    class Updated(Message):
        """Header 数据更新消息"""
        def __init__(self, summary: dict):
            super().__init__()
            self.summary = summary

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._refresh_timer = None

    def on_mount(self) -> None:
        """组件挂载时初始化"""
        self._refresh_data()
        # 设置定时刷新
        self._refresh_timer = self.set_interval(self.REFRESH_INTERVAL, self._refresh_data)

    def on_unmount(self) -> None:
        """组件卸载时清理"""
        if self._refresh_timer:
            self._refresh_timer.stop()

    def _refresh_data(self) -> None:
        """刷新数据"""
        try:
            summary = get_summary()
            self.workspace_size = summary.get("workspace_size_fmt", "0B")
            self.workspace_size_bytes = summary.get("workspace_size", 0)
            self.hidden_folders = summary.get("hidden_folders", 0)
            self.health_status = summary.get("health_status", "🟢")
            self.last_update = summary.get("timestamp", "")[-12:-7]  # 提取时间部分

            # 发送更新消息
            self.post_message(self.Updated(summary))
        except Exception as e:
            self.workspace_size = "Error"
            self.health_status = "⚠️"
            self.last_update = "Error"

    def _get_size_color(self) -> str:
        """根据大小获取颜色"""
        size = self.workspace_size_bytes
        if size < 500 * 1024 * 1024:  # <500MB
            return "green"
        elif size < 1024 * 1024 * 1024:  # <1GB
            return "yellow"
        else:
            return "red"

    def _get_size_style(self) -> Style:
        """获取大小显示样式"""
        return Style(color=self._get_size_color(), bold=True)

    def render(self) -> Text:
        """渲染 Header"""
        text = Text()

        # Logo
        text.append("🦞 ", style=Style(bold=True))
        text.append("Lobster Doctor", style=Style(bold=True, color="cyan"))
        text.append("  │  ")

        # 健康状态
        text.append(f"{self.health_status} ")

        # Workspace 大小（带颜色）
        text.append("Workspace: ", style=Style(color="white"))
        text.append(self.workspace_size, style=self._get_size_style())
        text.append("  │  ")

        # 隐藏文件夹
        text.append("📁 Hidden: ", style=Style(color="white"))
        hidden_color = "green" if self.hidden_folders <= 3 else ("yellow" if self.hidden_folders <= 5 else "red")
        text.append(str(self.hidden_folders), style=Style(color=hidden_color, bold=True))

        # 更新时间
        text.append("  │  ")
        text.append(f"🕐 {self.last_update}", style=Style(color="grey50"))

        return text


# 别名，方便导入
Header = HeaderWidget


if __name__ == "__main__":
    # 简单测试
    from textual.app import App, ComposeResult
    from textual.widgets import Footer

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield Footer()

    app = TestApp()
    app.run()
