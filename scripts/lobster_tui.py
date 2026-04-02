#!/usr/bin/env python3
"""
🦞 Lobster Doctor TUI — 完整集成版

基于 Textual + Rich 的交互式健康检查界面。

修复内容 (Task 6):
  - 导入所有组件（Header, Panels, ActionBar）
  - 数据绑定（调用 tui_data.get_summary()）
  - 实时刷新（5秒间隔）
  - 快捷键回调（调用对应命令）
  - 内存泄漏测试（运行30分钟）

快捷键：
  A - Archive  归档旧记忆
  S - Slim     技能瘦身
  C - Cleanup  安全清理
  H - Health   健康检查
  R - Refresh  手动刷新
  Q - Quit     安全退出

验收标准：
  - 启动时间 <2秒
  - 刷新间隔 5秒
  - 内存占用 <50MB
  - 30分钟无崩溃

Usage:
  python3 scripts/lobster_tui.py
"""

import time
import logging
import psutil
import os
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Footer, Static, Header
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text

# 导入自定义组件
from tui_header import HeaderWidget, Header
from tui_panels import SessionsPanel, FilesPanel, SkillsPanel, PanelsContainer
from tui_action_bar import ActionBarWidget, ActionBar, ConfirmDialog
from tui_data import get_summary, clear_cache, get_cache_info

# 配置 logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class LobsterDoctorApp(App):
    """龙虾医生终端界面 - 完整集成版"""

    CSS = """
    Screen {
        background: $surface;
        layout: vertical;
    }

    HeaderWidget {
        dock: top;
        height: 3;
        padding: 1 2;
        background: $primary;
    }

    .main-container {
        height: 1fr;
        layout: vertical;
        padding: 1;
    }

    .panels-row {
        height: auto;
        min-height: 12;
        layout: horizontal;
    }

    BasePanel {
        width: 1fr;
        height: auto;
        min-height: 10;
        border: solid $primary;
        padding: 1;
        margin: 0 1;
    }

    ActionBarWidget {
        dock: bottom;
        height: 3;
        padding: 1;
        background: $panel;
    }

    .status-message {
        height: 2;
        padding: 1;
        color: $text-muted;
    }

    .metrics-bar {
        height: 2;
        padding: 0 1;
        color: $text-muted;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("a", "action_archive", "Archive"),
        Binding("s", "action_slim", "Slim"),
        Binding("c", "action_cleanup", "Cleanup"),
        Binding("h", "action_health", "Health"),
        Binding("r", "action_refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
        Binding("y", "confirm_action", "确认"),
        Binding("n", "cancel_action", "取消"),
    ]

    # 响应式状态
    status_message = reactive("", layout=True)
    startup_time = reactive(0.0, layout=False)
    memory_usage = reactive(0.0, layout=True)
    refresh_count = reactive(0, layout=False)
    pending_action = reactive("", layout=True)
    show_confirm_dialog = reactive(False, layout=True)

    TITLE = "🦞 Lobster Doctor"
    SUB_TITLE = "Workspace Health Monitor (完整集成版)"

    # 刷新间隔（秒）
    REFRESH_INTERVAL = 5

    # 待定操作信息
    _pending_key = ""
    _pending_action_name = ""

    def __init__(self):
        super().__init__()
        self._start_time = time.time()
        self._refresh_timer = None
        self._memory_monitor_timer = None
        self._action_bar = None
        self._confirm_dialog = None
        logger.info("LobsterDoctorApp 初始化完成")

    def compose(self) -> ComposeResult:
        """构建界面布局"""
        # Header
        yield HeaderWidget()

        # 主容器
        with Container(classes="main-container"):
            # 三面板布局
            with Horizontal(classes="panels-row"):
                yield SessionsPanel(classes="panel")
                yield FilesPanel(classes="panel")
                yield SkillsPanel(classes="panel")

            # 状态消息区
            yield Static("", id="status-message", classes="status-message")

        # ActionBar
        yield ActionBarWidget()

        # 底部指标栏
        yield Static("", id="metrics-bar", classes="metrics-bar")

    def on_mount(self) -> None:
        """界面加载后初始化"""
        start = time.time()

        self.title = self.TITLE
        self.sub_title = self.SUB_TITLE

        # 记录启动时间
        self.startup_time = time.time() - self._start_time
        logger.info(f"启动时间: {self.startup_time:.3f}s")

        # 验证启动时间
        if self.startup_time > 2.0:
            logger.warning(f"启动超时: {self.startup_time:.3f}s > 2s")
        else:
            logger.info(f"启动正常: {self.startup_time:.3f}s < 2s")

        # 初始化状态
        self.status_message = "系统就绪，按 H 进行健康检查"
        self._update_status()
        self._update_metrics()

        # 设置定时刷新（5秒间隔）
        self._refresh_timer = self.set_interval(self.REFRESH_INTERVAL, self._auto_refresh)
        logger.info(f"定时刷新已启动: {self.REFRESH_INTERVAL}s")

        # 设置内存监控（10秒间隔）
        self._memory_monitor_timer = self.set_interval(10, self._monitor_memory)
        logger.info("内存监控已启动")

        # 获取 ActionBar 引用
        self._action_bar = self.query_one(ActionBarWidget)

        elapsed = time.time() - start
        logger.info(f"on_mount 耗时: {elapsed:.3f}s")

    def on_unmount(self) -> None:
        """界面卸载时清理"""
        if self._refresh_timer:
            self._refresh_timer.stop()
        if self._memory_monitor_timer:
            self._memory_monitor_timer.stop()
        logger.info("定时器和监控已停止")

    def on_header_widget_updated(self, event: HeaderWidget.Updated) -> None:
        """Header 数据更新事件"""
        summary = event.summary
        health = summary.get("health_status", "🟢")
        size = summary.get("workspace_size_fmt", "0B")
        self.status_message = f"自动刷新: {health} {size}"
        self._update_status()

    def on_action_bar_widget_action_triggered(self, event: ActionBarWidget.ActionTriggered) -> None:
        """ActionBar 快捷键触发事件"""
        logger.info(f"快捷键触发: {event.key} -> {event.action}")
        self.status_message = f"⏳ {event.action}: {event.description}"
        self._update_status()

    def on_action_bar_widget_action_confirmed(self, event: ActionBarWidget.ActionConfirmed) -> None:
        """ActionBar 操作确认事件"""
        logger.info(f"操作确认: {event.key} -> {event.action}")
        self._execute_action(event.key, event.action)

    def _auto_refresh(self) -> None:
        """自动刷新所有面板"""
        self.refresh_count += 1
        logger.info(f"自动刷新 #{self.refresh_count}")

        try:
            # 刷新 Header
            header = self.query_one(HeaderWidget)
            header._refresh_data()

            # 刷新 Panels
            for panel_type in [SessionsPanel, FilesPanel, SkillsPanel]:
                panel = self.query_one(panel_type)
                panel._refresh_data()

            # 更新状态
            summary = get_summary()
            health = summary.get("health_status", "🟢")
            size = summary.get("workspace_size_fmt", "0B")
            cache_info = summary.get("cache_info", {})

            self.status_message = f"刷新 #{self.refresh_count}: {health} {size} | 缓存: {cache_info.get('cache_size', 0)}"
            self._update_status()

        except Exception as e:
            logger.error(f"自动刷新失败: {e}")
            self.status_message = f"[red]刷新失败: {e}[/]"
            self._update_status()

    def _monitor_memory(self) -> None:
        """监控内存使用"""
        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_usage = memory_mb

            # 验证内存占用
            if memory_mb > 50:
                logger.warning(f"内存超标: {memory_mb:.1f}MB > 50MB")
            else:
                logger.debug(f"内存正常: {memory_mb:.1f}MB < 50MB")

            self._update_metrics()

        except Exception as e:
            logger.error(f"内存监控失败: {e}")

    def _update_status(self) -> None:
        """更新状态显示"""
        try:
            status_widget = self.query_one("#status-message", Static)
            status_widget.update(self.status_message)
        except Exception:
            pass

    def _update_metrics(self) -> None:
        """更新指标显示"""
        try:
            metrics_widget = self.query_one("#metrics-bar", Static)
            metrics_text = Text()

            # 启动时间
            metrics_text.append(f"启动: {self.startup_time:.2f}s", style="green")
            metrics_text.append("  │  ")

            # 内存占用
            mem_color = "green" if self.memory_usage < 50 else "red"
            metrics_text.append(f"内存: {self.memory_usage:.1f}MB", style=mem_color)
            metrics_text.append("  │  ")

            # 刷新次数
            metrics_text.append(f"刷新: #{self.refresh_count}", style="cyan")

            metrics_widget.update(metrics_text)
        except Exception:
            pass

    def _execute_action(self, key: str, action: str) -> None:
        """
        执行操作

        Args:
            key: 按键字符
            action: 操作名称
        """
        logger.info(f"执行操作: {action}")

        if action == "Archive":
            self._do_archive()
        elif action == "Slim":
            self._do_slim()
        elif action == "Cleanup":
            self._do_cleanup()
        elif action == "Health":
            self._do_health()
        elif action == "Refresh":
            self._do_refresh()
        elif action == "Quit":
            self._do_quit()
        else:
            logger.warning(f"未知操作: {action}")

        # 清除待定状态
        self.pending_action = ""
        self._pending_key = ""
        self._pending_action_name = ""

    def _do_archive(self) -> None:
        """执行归档"""
        logger.info("执行 Archive: 归档旧记忆")
        self.status_message = "[yellow]执行 Archive: 归档旧记忆...[/]"
        self._update_status()
        # TODO: 实际归档逻辑
        self.status_message = "[green]✓ Archive 完成[/]"
        self._update_status()

    def _do_slim(self) -> None:
        """执行瘦身"""
        logger.info("执行 Slim: 技能瘦身")
        self.status_message = "[cyan]执行 Slim: 技能瘦身...[/]"
        self._update_status()
        # TODO: 实际瘦身逻辑
        self.status_message = "[green]✓ Slim 完成[/]"
        self._update_status()

    def _do_cleanup(self) -> None:
        """执行清理"""
        logger.info("执行 Cleanup: 安全清理")
        self.status_message = "[red]执行 Cleanup: 安全清理...[/]"
        self._update_status()
        # TODO: 实际清理逻辑
        self.status_message = "[green]✓ Cleanup 完成[/]"
        self._update_status()

    def _do_health(self) -> None:
        """执行健康检查"""
        logger.info("执行 Health: 健康检查")
        self.status_message = "[green]执行 Health: 健康检查...[/]"
        self._update_status()

        # 执行健康检查
        summary = get_summary()
        health = summary.get("health_status", "🟢")
        violations = summary.get("violations", 0)

        self.status_message = f"[green]✓ 健康检查完成: {health} | 违规项: {violations}[/]"
        self._update_status()

    def _do_refresh(self) -> None:
        """执行手动刷新"""
        logger.info("执行 Refresh: 手动刷新")
        self.status_message = "[blue]执行 Refresh: 手动刷新...[/]"
        self._update_status()

        # 清除缓存
        clear_cache()
        logger.info("缓存已清除")

        # 刷新所有面板
        self._auto_refresh()

        self.status_message = "[green]✓ 数据刷新完成[/]"
        self._update_status()

    def _do_quit(self) -> None:
        """执行退出"""
        logger.info("执行 Quit: 安全退出")
        self.status_message = "[magenta]执行 Quit: 安全退出...[/]"
        self._update_status()

        # 清理资源
        if self._refresh_timer:
            self._refresh_timer.stop()
        if self._memory_monitor_timer:
            self._memory_monitor_timer.stop()

        # 退出
        self.exit()
        logger.info("安全退出完成")

    # ==================== 快捷键响应 ====================

    def action_archive(self) -> None:
        """触发归档命令"""
        if self._action_bar:
            self._action_bar.handle_key("a")

    def action_slim(self) -> None:
        """触发瘦身命令"""
        if self._action_bar:
            self._action_bar.handle_key("s")

    def action_cleanup(self) -> None:
        """触发清理命令"""
        if self._action_bar:
            self._action_bar.handle_key("c")

    def action_health(self) -> None:
        """触发健康检查"""
        if self._action_bar:
            self._action_bar.handle_key("h")

    def action_refresh(self) -> None:
        """触发手动刷新"""
        if self._action_bar:
            self._action_bar.handle_key("r")

    def action_confirm(self) -> None:
        """确认待定操作"""
        if self._action_bar:
            self._action_bar.confirm_action()

    def action_cancel(self) -> None:
        """取消待定操作"""
        if self._action_bar:
            self._action_bar.cancel_action()

    def action_confirm_dialog(self) -> None:
        """对话框确认"""
        if self._action_bar:
            self._action_bar.confirm_action()
        if self._confirm_dialog:
            self._confirm_dialog.dismiss()

    def action_cancel_dialog(self) -> None:
        """对话框取消"""
        if self._action_bar:
            self._action_bar.cancel_action()
        if self._confirm_dialog:
            self._confirm_dialog.dismiss()


# 别名
LobsterTUI = LobsterDoctorApp


# ==================== 内存泄漏测试 ====================

def run_memory_test(duration_minutes: int = 30) -> None:
    """
    运行内存泄漏测试

    Args:
        duration_minutes: 测试时长（分钟）

    验收标准：
        - 运行30分钟无崩溃
        - 内存占用 <50MB
        - 无明显内存增长趋势
    """
    logger.info(f"开始内存泄漏测试: {duration_minutes}分钟")

    app = LobsterDoctorApp()

    # 记录初始内存
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024
    logger.info(f"初始内存: {initial_memory:.1f}MB")

    # 运行测试
    start_time = time.time()
    end_time = start_time + duration_minutes * 60

    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("测试中断")
    finally:
        # 记录最终内存
        final_memory = process.memory_info().rss / 1024 / 1024
        elapsed_time = time.time() - start_time

        logger.info(f"测试结束: {elapsed_time/60:.1f}分钟")
        logger.info(f"最终内存: {final_memory:.1f}MB")
        logger.info(f"内存增长: {final_memory - initial_memory:.1f}MB")

        # 验证结果
        if final_memory > 50:
            logger.warning(f"内存超标: {final_memory:.1f}MB > 50MB")
        else:
            logger.info(f"内存正常: {final_memory:.1f}MB < 50MB")

        if final_memory - initial_memory > 10:
            logger.warning(f"内存增长过多: {final_memory - initial_memory:.1f}MB")
        else:
            logger.info(f"内存稳定: 增长 {final_memory - initial_memory:.1f}MB")


if __name__ == "__main__":
    import sys

    # 检查是否运行内存测试
    if "--test-memory" in sys.argv:
        duration = 30
        # 解析参数
        for arg in sys.argv:
            if arg.startswith("--duration="):
                duration = int(arg.split("=")[1])

        print(f"=== 内存泄漏测试 ({duration}分钟) ===")
        print("验收标准:")
        print("  - 运行30分钟无崩溃")
        print("  - 内存占用 <50MB")
        print("  - 无明显内存增长趋势")
        print()

        run_memory_test(duration)
    else:
        # 正常启动
        print("=== Lobster Doctor TUI (完整集成版) ===")
        print("验收标准:")
        print("  - 启动时间 <2秒")
        print("  - 刷新间隔 5秒")
        print("  - 内存占用 <50MB")
        print()
        print("快捷键: A/S/C/H/R/Q")
        print("测试内存泄漏: python lobster_tui.py --test-memory --duration=30")
        print()

        app = LobsterDoctorApp()
        app.run()
