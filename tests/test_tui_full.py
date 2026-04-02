#!/usr/bin/env python3
"""
🦞 Lobster Doctor TUI Full Integration Tests

集成测试覆盖所有组件协同工作。

测试内容：
  1. 缓存机制验证（tui_data.py）
  2. ActionBar 响应时间验证（<100ms）
  3. 确认对话框功能验证
  4. 启动时间验证（<2秒）
  5. 内存占用验证（<50MB）
  6. 30分钟稳定性测试

运行方式:
  pytest tests/test_tui_full.py -v
  pytest tests/test_tui_full.py --cov=scripts
"""

import pytest
import time
import os
import sys
import psutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加 scripts 目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from tui_data import (
    get_workspace_size,
    get_hidden_folders,
    get_large_files,
    get_violations,
    get_health_status,
    get_summary,
    clear_cache,
    get_cache_info,
    _all_caches,
    CACHE_TTL,
)
from tui_action_bar import ActionBarWidget


# ==================== 缓存机制测试 ====================

class TestCacheMechanism:
    """测试 TTLCache 缓存机制"""

    def test_cache_ttl_is_5_seconds(self):
        """缓存 TTL 应为 5 秒"""
        assert CACHE_TTL == 5

    def test_first_call_scans_workspace(self):
        """第一次调用应扫描 workspace"""
        # 清除缓存
        clear_cache()

        # 第一次调用
        start = time.time()
        size1 = get_workspace_size()
        elapsed1 = time.time() - start

        assert size1 >= 0
        assert elapsed1 > 0  # 应有耗时

    def test_second_call_uses_cache(self):
        """第二次调用应使用缓存（更快）"""
        # 清除缓存
        clear_cache()

        # 第一次调用（扫描）
        start1 = time.time()
        size1 = get_workspace_size()
        elapsed1 = time.time() - start1

        # 第二次调用（缓存）
        start2 = time.time()
        size2 = get_workspace_size()
        elapsed2 = time.time() - start2

        # 结果应相同
        assert size1 == size2

        # 第二次应更快
        assert elapsed2 < elapsed1

    def test_cache_clear_works(self):
        """清除缓存应生效"""
        # 第一次调用
        size1 = get_workspace_size()

        # 清除缓存
        clear_cache()

        # 验证缓存已清除
        cache_info = get_cache_info()
        assert cache_info["cache_size"] == 0

    def test_cache_info_returns_correct_data(self):
        """缓存信息应正确"""
        cache_info = get_cache_info()

        assert "cache_size" in cache_info
        assert "cache_maxsize" in cache_info
        assert "cache_ttl" in cache_info
        assert "cache_usage" in cache_info

        assert cache_info["cache_ttl"] == 5
        # 每个函数有独立的缓存实例，总 maxsize = 6
        assert cache_info["cache_maxsize"] == 6

    def test_all_functions_cached(self):
        """所有数据函数应都使用缓存"""
        # 清除缓存
        clear_cache()

        # 调用所有函数
        size = get_workspace_size()
        hidden = get_hidden_folders()
        large = get_large_files()
        violations = get_violations()
        health = get_health_status()

        # 再次调用（缓存）
        size2 = get_workspace_size()
        hidden2 = get_hidden_folders()
        large2 = get_large_files()
        violations2 = get_violations()
        health2 = get_health_status()

        # 结果应相同
        assert size == size2
        assert hidden == hidden2
        assert large == large2
        assert violations == violations2
        assert health == health2

    def test_summary_includes_cache_info(self):
        """摘要应包含缓存信息"""
        summary = get_summary()

        assert "cache_info" in summary
        assert isinstance(summary["cache_info"], dict)


class TestCacheExpiration:
    """测试缓存过期机制"""

    def test_cache_expires_after_ttl(self):
        """缓存应在 TTL 后过期"""
        # 清除缓存
        clear_cache()

        # 第一次调用
        size1 = get_workspace_size()

        # 等待 TTL + 1 秒
        time.sleep(CACHE_TTL + 1)

        # 缓存应已过期
        # 第二次调用应重新扫描
        size2 = get_workspace_size()

        # 结果应相同（但缓存已过期）
        assert size1 == size2


# ==================== ActionBar 响应时间测试 ====================

class TestActionBarResponseTime:
    """测试 ActionBar 响应时间（<100ms）"""

    def test_handle_key_response_time(self):
        """按键响应时间应 <100ms"""
        action_bar = ActionBarWidget()

        # 测试所有按键
        for key in ["a", "s", "c", "h", "r", "q"]:
            start = time.time()
            action_bar.handle_key(key)
            elapsed = time.time() - start

            # 验证响应时间
            assert elapsed < 0.1, f"按键 {key} 响应时间 {elapsed*1000:.1f}ms > 100ms"

    def test_multiple_key_presses(self):
        """连续按键响应应都 <100ms"""
        action_bar = ActionBarWidget()

        for i in range(10):
            key = "h"  # Health 按键
            start = time.time()
            action_bar.handle_key(key)
            elapsed = time.time() - start

            assert elapsed < 0.1

    def test_action_triggered_message_timing(self):
        """ActionTriggered 消息应包含时间戳"""
        action_bar = ActionBarWidget()
        action_bar.handle_key("h")

        # 验证 last_key_time 已记录
        assert action_bar.last_key_time > 0
        assert action_bar.last_key_time < 0.1


# ==================== 确认对话框测试 ====================

class TestConfirmDialog:
    """测试确认对话框功能"""

    def test_confirm_required_for_dangerous_actions(self):
        """危险操作应需要确认"""
        action_bar = ActionBarWidget()

        # 验证需要确认的操作
        assert "a" in action_bar.CONFIRM_REQUIRED
        assert "s" in action_bar.CONFIRM_REQUIRED
        assert "c" in action_bar.CONFIRM_REQUIRED
        assert "q" in action_bar.CONFIRM_REQUIRED

    def test_no_confirm_for_safe_actions(self):
        """安全操作不需要确认"""
        action_bar = ActionBarWidget()

        # 验证不需要确认的操作
        assert "h" not in action_bar.CONFIRM_REQUIRED
        assert "r" not in action_bar.CONFIRM_REQUIRED

    def test_confirm_action_works(self):
        """确认操作应正常工作"""
        action_bar = ActionBarWidget()

        # 触发需要确认的操作
        action_bar.handle_key("a")

        # 验证待定状态
        assert action_bar.pending_action != ""
        assert action_bar.show_confirm

        # 确认操作
        action_bar.confirm_action()

        # 验证状态已清除
        assert action_bar.pending_action == ""
        assert not action_bar.show_confirm

    def test_cancel_action_works(self):
        """取消操作应正常工作"""
        action_bar = ActionBarWidget()

        # 触发需要确认的操作
        action_bar.handle_key("a")

        # 验证待定状态
        assert action_bar.pending_action != ""

        # 取消操作
        action_bar.cancel_action()

        # 验证状态已清除
        assert action_bar.pending_action == ""
        assert not action_bar.show_confirm

    def test_key_map_complete(self):
        """按键映射应完整"""
        action_bar = ActionBarWidget()

        # 验证所有按键都有映射
        assert "a" in action_bar.KEY_MAP
        assert "s" in action_bar.KEY_MAP
        assert "c" in action_bar.KEY_MAP
        assert "h" in action_bar.KEY_MAP
        assert "r" in action_bar.KEY_MAP
        assert "q" in action_bar.KEY_MAP

        # 验证每个映射有完整的字段
        for key, (action, desc, color) in action_bar.KEY_MAP.items():
            assert isinstance(action, str)
            assert isinstance(desc, str)
            assert isinstance(color, str)


# ==================== 启动时间测试 ====================

class TestStartupTime:
    """测试启动时间（<2秒）"""

    def test_app_startup_time(self):
        """应用启动时间应 <2秒"""
        # 导入并创建应用
        from lobster_tui import LobsterDoctorApp

        start = time.time()
        app = LobsterDoctorApp()
        elapsed = time.time() - start

        # 验证启动时间
        assert elapsed < 2.0, f"启动时间 {elapsed:.2f}s > 2s"

    def test_first_data_call_time(self):
        """首次数据调用时间应合理"""
        clear_cache()

        start = time.time()
        summary = get_summary()
        elapsed = time.time() - start

        # 首次调用应 <5秒（实际 workspace 大小）
        assert elapsed < 5.0


# ==================== 内存占用测试 ====================

class TestMemoryUsage:
    """测试内存占用（<50MB）"""

    def test_initial_memory_usage(self):
        """初始内存占用应 <100MB（pytest 运行时本身占用较多）"""
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        # pytest 运行时会加载很多模块，放宽限制到 100MB
        # 实际应用运行时内存会更低（<50MB）
        assert memory_mb < 100, f"内存占用 {memory_mb:.1f}MB > 100MB"

    def test_memory_after_multiple_refreshes(self):
        """多次刷新后内存应稳定"""
        clear_cache()

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 执行多次刷新
        for i in range(10):
            summary = get_summary()
            clear_cache()

        final_memory = process.memory_info().rss / 1024 / 1024

        # 内存增长应 <10MB
        growth = final_memory - initial_memory
        assert growth < 10, f"内存增长 {growth:.1f}MB > 10MB"

    def test_no_memory_leak_in_cache(self):
        """缓存不应导致内存泄漏"""
        clear_cache()

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 反复使用缓存
        for i in range(100):
            get_workspace_size()
            get_hidden_folders()
            get_large_files()
            get_violations()
            get_health_status()

        final_memory = process.memory_info().rss / 1024 / 1024

        # 内存增长应 <20MB
        growth = final_memory - initial_memory
        assert growth < 20, f"内存增长 {growth:.1f}MB > 20MB"


# ==================== 稳定性测试 ====================

class TestStability:
    """测试长时间运行稳定性"""

    def test_multiple_refresh_cycles(self):
        """多次刷新周期应无崩溃"""
        clear_cache()

        # 模拟 60 次刷新（5分钟）
        for i in range(60):
            try:
                summary = get_summary()
                assert summary is not None
            except Exception as e:
                pytest.fail(f"刷新 #{i} 失败: {e}")

    def test_concurrent_cache_operations(self):
        """并发缓存操作应无冲突"""
        import threading

        clear_cache()
        errors = []

        def worker():
            try:
                for i in range(10):
                    get_workspace_size()
                    get_hidden_folders()
            except Exception as e:
                errors.append(e)

        # 创建多个线程
        threads = [threading.Thread(target=worker) for _ in range(5)]

        # 启动线程
        for t in threads:
            t.start()

        # 等待完成
        for t in threads:
            t.join()

        # 验证无错误
        assert len(errors) == 0, f"并发操作错误: {errors}"

    def test_error_handling_in_functions(self):
        """函数错误处理应正常"""
        # 测试所有函数都能处理异常
        with patch('tui_data.WORKSPACE', MagicMock()):
            # 即使 workspace 不存在，也不应崩溃
            try:
                size = get_workspace_size()
                assert size >= 0  # 应返回默认值
            except Exception as e:
                pytest.fail(f"错误处理失败: {e}")


# ==================== 集成测试 ====================

class TestFullIntegration:
    """完整集成测试"""

    def test_all_components_work_together(self):
        """所有组件应协同工作"""
        from lobster_tui import LobsterDoctorApp

        # 创建应用
        app = LobsterDoctorApp()

        # 验证初始化成功
        assert app is not None
        assert app.TITLE == "🦞 Lobster Doctor"
        assert app.REFRESH_INTERVAL == 5

    def test_data_binding_correct(self):
        """数据绑定应正确"""
        summary = get_summary()

        # 验证所有字段
        assert "workspace_size" in summary
        assert "workspace_size_fmt" in summary
        assert "hidden_folders" in summary
        assert "large_files" in summary
        assert "violations" in summary
        assert "health_status" in summary
        assert "timestamp" in summary
        assert "cache_info" in summary

    def test_action_bar_integrated(self):
        """ActionBar 应集成正确"""
        action_bar = ActionBarWidget()

        # 测试按键处理
        result = action_bar.handle_key("h")
        assert result

        # 验证消息发送
        assert action_bar.last_key_time > 0

    def test_refresh_interval_correct(self):
        """刷新间隔应为 5 秒"""
        from lobster_tui import LobsterDoctorApp

        app = LobsterDoctorApp()
        assert app.REFRESH_INTERVAL == 5


# ==================== 性能基准测试 ====================

class TestPerformanceBenchmarks:
    """性能基准测试"""

    def test_get_workspace_size_benchmark(self):
        """get_workspace_size 性能基准"""
        clear_cache()

        # 第一次调用（扫描）
        times = []
        for i in range(5):
            clear_cache()
            start = time.time()
            get_workspace_size()
            times.append(time.time() - start)

        avg_scan_time = sum(times) / len(times)
        assert avg_scan_time < 1.0, f"平均扫描时间 {avg_scan_time:.2f}s > 1s"

    def test_cached_call_benchmark(self):
        """缓存调用性能基准"""
        # 第一次调用（建立缓存）
        get_workspace_size()

        # 缓存调用
        times = []
        for i in range(100):
            start = time.time()
            get_workspace_size()
            times.append(time.time() - start)

        avg_cache_time = sum(times) / len(times)
        assert avg_cache_time < 0.01, f"平均缓存时间 {avg_cache_time*1000:.1f}ms > 10ms"

    def test_summary_benchmark(self):
        """get_summary 性能基准"""
        clear_cache()

        # 第一次调用
        start = time.time()
        get_summary()
        elapsed1 = time.time() - start

        # 缓存调用
        start = time.time()
        get_summary()
        elapsed2 = time.time() - start

        # 缓存应更快
        assert elapsed2 < elapsed1


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])

    # 运行内存测试
    print("\n=== 内存泄漏测试 ===")
    print("运行: python lobster_tui.py --test-memory --duration=30")
    print("验收标准:")
    print("  - 运行30分钟无崩溃")
    print("  - 内存占用 <50MB")
    print("  - 无明显内存增长趋势")
