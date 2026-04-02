#!/usr/bin/env python3
"""
🦞 Lobster Doctor TUI ActionBar Component

ActionBar 组件：显示快捷键提示和响应按键操作。

功能：
  - Footer 类（继承 Widget）
  - 快捷键绑定（A/S/C/H/R/Q）
  - 按键提示显示
  - 确认对话框（防止误操作）
  - 按键响应回调

快捷键：
  A - Archive  归档旧记忆
  S - Slim     技能瘦身
  C - Cleanup  安全清理
  H - Health   健康检查
  R - Refresh  手动刷新
  Q - Quit     安全退出

验收标准：
  - 快捷键响应 <100ms
  - 确认对话框弹出正常
  - 取消操作正常
"""

from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Static, Button
from textual.binding import Binding
from rich.text import Text
from rich.style import Style
import time
import logging

logger = logging.getLogger(__name__)


class ActionBarWidget(Widget):
    """
    ActionBar 组件

    显示快捷键提示，响应按键操作。
    快捷键响应时间 <100ms。
    """

    # 响应式状态
    last_key_time = reactive(0.0, layout=False)
    pending_action = reactive("", layout=True)
    show_confirm = reactive(False, layout=True)

    # 快捷键映射
    KEY_MAP = {
        "a": ("Archive", "归档旧记忆", "yellow"),
        "s": ("Slim", "技能瘦身", "cyan"),
        "c": ("Cleanup", "安全清理", "red"),
        "h": ("Health", "健康检查", "green"),
        "r": ("Refresh", "手动刷新", "blue"),
        "q": ("Quit", "安全退出", "magenta"),
    }

    # 需要确认的危险操作
    CONFIRM_REQUIRED = {"a", "s", "c", "q"}

    class ActionTriggered(Message):
        """快捷键触发消息"""
        def __init__(self, key: str, action: str, description: str):
            super().__init__()
            self.key = key
            self.action = action
            self.description = description
            self.timestamp = time.time()

    class ActionConfirmed(Message):
        """操作确认消息"""
        def __init__(self, key: str, action: str):
            super().__init__()
            self.key = key
            self.action = action

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pending_key = ""
        self._pending_action = ""
        self._start_time = 0.0

    def on_mount(self) -> None:
        """组件挂载时初始化"""
        logger.info("ActionBar 已挂载")

    def handle_key(self, key: str) -> bool:
        """
        处理按键输入

        Args:
            key: 按键字符

        Returns:
            bool: 是否成功处理

        性能要求：<100ms 响应时间
        """
        start_time = time.time()
        self._start_time = start_time

        if key not in self.KEY_MAP:
            logger.debug(f"忽略无效按键: {key}")
            return False

        action, desc, color = self.KEY_MAP[key]
        logger.info(f"按键触发: {key} -> {action}")

        # 记录响应时间
        elapsed = time.time() - start_time
        self.last_key_time = elapsed

        if elapsed > 0.1:  # >100ms
            logger.warning(f"按键响应超时: {elapsed:.3f}s")
        else:
            logger.debug(f"按键响应时间: {elapsed:.3f}s")

        # 发送触发消息
        self.post_message(self.ActionTriggered(key, action, desc))

        # 需要确认的操作
        if key in self.CONFIRM_REQUIRED:
            self._pending_key = key
            self._pending_action = action
            self.pending_action = f"{action}: {desc}"
            self.show_confirm = True
            logger.info(f"等待确认: {action}")
        else:
            # 直接执行（H/R）
            self._execute_action(key, action)

        return True

    def _execute_action(self, key: str, action: str) -> None:
        """
        执行操作

        Args:
            key: 按键字符
            action: 操作名称
        """
        logger.info(f"执行操作: {action}")
        self.post_message(self.ActionConfirmed(key, action))
        self._clear_pending()

    def confirm_action(self) -> None:
        """
        确认执行待定操作
        """
        if self._pending_key and self._pending_action:
            logger.info(f"确认执行: {self._pending_action}")
            self._execute_action(self._pending_key, self._pending_action)

    def cancel_action(self) -> None:
        """
        取消待定操作
        """
        logger.info(f"取消操作: {self._pending_action}")
        self._clear_pending()

    def _clear_pending(self) -> None:
        """
        清除待定状态
        """
        self._pending_key = ""
        self._pending_action = ""
        self.pending_action = ""
        self.show_confirm = False

    def render(self) -> Text:
        """
        渲染 ActionBar

        显示快捷键提示和待定操作状态。
        """
        text = Text()

        # 快捷键提示
        text.append("快捷键: ", style=Style(color="white", bold=True))

        for key, (action, desc, color) in self.KEY_MAP.items():
            # 按键高亮显示
            text.append(f"[", style=Style(color="white"))
            text.append(key.upper(), style=Style(color=color, bold=True))
            text.append("]", style=Style(color="white"))
            text.append(f" {action}  ", style=Style(color=color))

        # 显示待定操作
        if self.pending_action:
            text.append("  │  ", style=Style(color="grey50"))
            text.append("⏳ ", style=Style(color="yellow"))
            text.append(self.pending_action, style=Style(color="yellow", bold=True))
            text.append("  [Y]确认 [N]取消", style=Style(color="grey50"))

        # 显示响应时间（调试）
        if self.last_key_time > 0:
            text.append("  │  ", style=Style(color="grey50"))
            if self.last_key_time < 0.1:
                text.append(f"⚡{self.last_key_time*1000:.1f}ms", style=Style(color="green"))
            else:
                text.append(f"⚠️{self.last_key_time*1000:.1f}ms", style=Style(color="red"))

        return text


class ConfirmDialog(ModalScreen):
    """
    确认对话框

    用于危险操作的二次确认。
    """

    CSS = """
    ConfirmDialog {
        align: center middle;
        width: 60;
        height: 10;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }

    ConfirmDialog > Static {
        text-align: center;
        height: auto;
    }

    ConfirmDialog > Horizontal {
        height: auto;
        align: center middle;
        padding: 1;
    }

    ConfirmDialog Button {
        width: 20;
        margin: 1;
    }

    .confirm-btn {
        background: $success;
    }

    .cancel-btn {
        background: $error;
    }
    """

    def __init__(self, action: str, description: str, **kwargs):
        super().__init__(**kwargs)
        self._action = action
        self._description = description

    def compose(self):
        """构建对话框布局"""
        yield Static(
            f"确认执行操作？\n\n{self._action}: {self._description}",
            classes="dialog-message"
        )
        with Static(classes="dialog-buttons"):
            yield Button("✓ 确认 (Y)", classes="confirm-btn", id="confirm-btn")
            yield Button("✗ 取消 (N)", classes="cancel-btn", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """按钮点击事件"""
        if event.button.id == "confirm-btn":
            logger.info(f"对话框确认: {self._action}")
            self.app.action_confirm_dialog()
        else:
            logger.info(f"对话框取消: {self._action}")
            self.app.action_cancel_dialog()
        self.dismiss()

    def on_key(self, event) -> None:
        """按键事件"""
        if event.key == "y":
            logger.info(f"按键确认: {self._action}")
            self.app.action_confirm_dialog()
            self.dismiss()
        elif event.key == "n" or event.key == "escape":
            logger.info(f"按键取消: {self._action}")
            self.app.action_cancel_dialog()
            self.dismiss()


# 别名
ActionBar = ActionBarWidget


if __name__ == "__main__":
    # 简单测试
    from textual.app import App, ComposeResult
    from textual.widgets import Header
    import time

    class TestApp(App):
        CSS = """
        Screen {
            layout: vertical;
        }

        ActionBarWidget {
            dock: bottom;
            height: 3;
            padding: 1;
            background: $panel;
        }
        """

        BINDINGS = [
            Binding("a", "test_archive", "Archive"),
            Binding("s", "test_slim", "Slim"),
            Binding("c", "test_cleanup", "Cleanup"),
            Binding("h", "test_health", "Health"),
            Binding("r", "test_refresh", "Refresh"),
            Binding("q", "test_quit", "Quit"),
        ]

        def compose(self) -> ComposeResult:
            yield Header()
            yield ActionBarWidget()

        def action_test_archive(self) -> None:
            """测试 Archive"""
            action_bar = self.query_one(ActionBarWidget)
            action_bar.handle_key("a")

        def action_test_slim(self) -> None:
            """测试 Slim"""
            action_bar = self.query_one(ActionBarWidget)
            action_bar.handle_key("s")

        def action_test_cleanup(self) -> None:
            """测试 Cleanup"""
            action_bar = self.query_one(ActionBarWidget)
            action_bar.handle_key("c")

        def action_test_health(self) -> None:
            """测试 Health"""
            action_bar = self.query_one(ActionBarWidget)
            action_bar.handle_key("h")

        def action_test_refresh(self) -> None:
            """测试 Refresh"""
            action_bar = self.query_one(ActionBarWidget)
            action_bar.handle_key("r")

        def action_test_quit(self) -> None:
            """测试 Quit"""
            action_bar = self.query_one(ActionBarWidget)
            action_bar.handle_key("q")

        def action_confirm_dialog(self) -> None:
            """确认对话框"""
            action_bar = self.query_one(ActionBarWidget)
            action_bar.confirm_action()
            self.notify("操作已确认执行", title="确认")

        def action_cancel_dialog(self) -> None:
            """取消对话框"""
            action_bar = self.query_one(ActionBarWidget)
            action_bar.cancel_action()
            self.notify("操作已取消", title="取消")

        def on_action_bar_widget_action_triggered(self, event: ActionBarWidget.ActionTriggered) -> None:
            """快捷键触发事件"""
            self.notify(f"{event.action}: {event.description}", title=f"按键 {event.key.upper()}")
            logger.info(f"响应时间: {event.timestamp - self._start_time:.3f}s")

    print("=== ActionBar 组件测试 ===")
    print("快捷键: A/S/C/H/R/Q")
    print("性能要求: 响应时间 <100ms")
    print()

    app = TestApp()
    app.run()
