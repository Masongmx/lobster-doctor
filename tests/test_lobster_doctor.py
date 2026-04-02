#!/usr/bin/env python3
"""
Lobster Doctor 单元测试

测试内容：
1. 相对阈值计算
2. 孤立进程检测
3. 内存泄漏警告
4. Token 计数器验证
5. 边界条件
6. 异常处理
"""

import sys
import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# 导入被测试的模块
import lobster_doctor as ld


class TestRelativeThreshold:
    """测试相对阈值计算"""
    
    def test_default_context_window(self):
        """测试默认上下文窗口"""
        window = ld.get_model_context_window()
        assert window > 0, "上下文窗口应大于0"
        assert window == 128_000, "默认上下文窗口应为128K"
    
    def test_gpt4o_context_window(self):
        """测试 GPT-4o 上下文窗口"""
        window = ld.get_model_context_window("gpt-4o")
        assert window == 128_000, "GPT-4o 上下文窗口应为128K"
    
    def test_claude_context_window(self):
        """测试 Claude 上下文窗口"""
        window = ld.get_model_context_window("claude-3-opus")
        assert window == 200_000, "Claude-3-Opus 上下文窗口应为200K"
    
    def test_relative_threshold_healthy(self):
        """测试健康状态阈值"""
        # 使用10%的上下文窗口
        tokens = 12_800  # 128K * 10%
        result = ld.calculate_relative_threshold(tokens, "gpt-4o")
        assert result["status"] == "healthy", "10%使用率应为健康状态"
        assert result["percentage"] == 10.0
    
    def test_relative_threshold_notice(self):
        """测试注意状态阈值"""
        # 使用60%的上下文窗口
        tokens = 76_800  # 128K * 60%
        result = ld.calculate_relative_threshold(tokens, "gpt-4o")
        assert result["status"] == "notice", "60%使用率应为注意状态"
    
    def test_relative_threshold_warning(self):
        """测试警告状态阈值"""
        # 使用80%的上下文窗口
        tokens = 102_400  # 128K * 80%
        result = ld.calculate_relative_threshold(tokens, "gpt-4o")
        assert result["status"] == "warning", "80%使用率应为警告状态"
    
    def test_relative_threshold_danger(self):
        """测试危险状态阈值"""
        # 使用90%的上下文窗口
        tokens = 115_200  # 128K * 90%
        result = ld.calculate_relative_threshold(tokens, "gpt-4o")
        assert result["status"] == "danger", "90%使用率应为危险状态"
    
    def test_remaining_tokens(self):
        """测试剩余 token 计算"""
        tokens = 50_000
        result = ld.calculate_relative_threshold(tokens, "gpt-4o")
        expected_remaining = 128_000 - 50_000
        assert result["remaining"] == expected_remaining
    
    def test_threshold_percentages_sum(self):
        """测试阈值百分比配置合理性"""
        config = ld.THRESHOLD_PERCENTAGES
        # 阈值应该递增
        assert config["healthy"] < config["notice"] < config["warning"] < config["danger"]


class TestOrphanProcessDetection:
    """测试孤立进程检测"""
    
    def test_detect_returns_list(self):
        """测试返回类型"""
        result = ld.detect_orphan_processes()
        assert isinstance(result, list), "应返回列表"
    
    def test_detect_handles_error(self):
        """测试错误处理"""
        # 即使系统调用失败，也应该返回列表（可能包含错误信息）
        result = ld.detect_orphan_processes()
        assert isinstance(result, list)


class TestMemoryLeakDetection:
    """测试内存泄漏检测"""
    
    def test_check_returns_dict(self):
        """测试返回类型"""
        result = ld.check_memory_leak()
        assert isinstance(result, dict), "应返回字典"
        assert "warnings" in result, "应包含 warnings 字段"
        assert "memory_usage" in result, "应包含 memory_usage 字段"
    
    def test_warnings_is_list(self):
        """测试警告列表"""
        result = ld.check_memory_leak()
        assert isinstance(result["warnings"], list), "warnings 应为列表"


class TestTokenCounterVerification:
    """测试 Token 计数器验证"""
    
    def test_verify_returns_dict(self):
        """测试返回类型"""
        result = ld.verify_token_counter()
        assert isinstance(result, dict), "应返回字典"
        assert "status" in result, "应包含 status 字段"
        assert "anomalies" in result, "应包含 anomalies 字段"
    
    def test_status_is_valid(self):
        """测试状态值有效"""
        result = ld.verify_token_counter()
        assert result["status"] in ["ok", "anomalies_found"]


class TestArchiveFunction:
    """测试 Memory 归档功能"""
    
    def test_archive_dir_defined(self):
        """测试归档目录定义"""
        assert hasattr(ld, "ARCHIVE_DIR"), "应定义 ARCHIVE_DIR"
    
    def test_archive_threshold_days(self):
        """测试归档阈值天数"""
        # 默认应为30天
        pass  # 实际测试需要模拟文件系统


class TestModelContextWindows:
    """测试模型上下文窗口配置"""
    
    def test_all_models_have_positive_window(self):
        """测试所有模型的上下文窗口为正数"""
        for model, window in ld.MODEL_CONTEXT_WINDOWS.items():
            assert window > 0, f"{model} 的上下文窗口应为正数"
    
    def test_default_model_exists(self):
        """测试默认模型存在"""
        assert "default" in ld.MODEL_CONTEXT_WINDOWS, "应包含 default 模型配置"


class TestThresholdPercentages:
    """测试阈值百分比配置"""
    
    def test_all_percentages_between_0_and_1(self):
        """测试所有阈值百分比在0-1之间"""
        for name, value in ld.THRESHOLD_PERCENTAGES.items():
            assert 0 < value <= 1, f"{name} 阈值应在(0,1]之间"
    
    def test_percentages_ascending(self):
        """测试阈值百分比递增"""
        config = ld.THRESHOLD_PERCENTAGES
        assert config["healthy"] < config["notice"]
        assert config["notice"] < config["warning"]
        assert config["warning"] < config["danger"]


class TestProtectedFiles:
    """测试受保护文件配置"""
    
    def test_core_files_defined(self):
        """测试核心文件白名单定义"""
        assert hasattr(ld, "CORE_FILES"), "应定义 CORE_FILES"
        assert len(ld.CORE_FILES) > 0, "核心文件白名单不应为空"
    
    def test_important_files_in_whitelist(self):
        """测试重要文件在白名单中"""
        important_files = ["MEMORY.md", "AGENTS.md", "SOUL.md", "USER.md"]
        for f in important_files:
            assert f in ld.CORE_FILES, f"{f} 应在白名单中"
    
    def test_protected_dirs_defined(self):
        """测试受保护目录定义"""
        assert hasattr(ld, "PROTECTED_DIRS"), "应定义 PROTECTED_DIRS"


class TestEdgeCases:
    """边界条件测试"""
    
    def test_relative_threshold_zero_tokens(self):
        """测试零 token 的阈值"""
        result = ld.calculate_relative_threshold(0)
        assert result["percentage"] == 0.0
        assert result["status"] == "healthy"
    
    def test_relative_threshold_full_window(self):
        """测试100%使用的阈值"""
        window = ld.get_model_context_window("gpt-4o")
        result = ld.calculate_relative_threshold(window, "gpt-4o")
        assert result["percentage"] == 100.0
        assert result["status"] == "danger"
    
    def test_relative_threshold_exceeds_window(self):
        """测试超过上下文窗口的情况"""
        window = ld.get_model_context_window("gpt-4o")
        result = ld.calculate_relative_threshold(window * 2, "gpt-4o")
        assert result["percentage"] > 100
        assert result["status"] == "danger"
    
    def test_unknown_model_uses_default(self):
        """测试未知模型使用默认窗口"""
        window = ld.get_model_context_window("unknown-model-xyz")
        assert window == ld.MODEL_CONTEXT_WINDOWS["default"]


class TestIntegration:
    """集成测试"""
    
    def test_health_check_runs(self):
        """测试健康检查可以运行"""
        # 创建模拟的 args
        class Args:
            json = False
        
        # 这个测试只是验证函数不会崩溃
        try:
            ld.cmd_health(Args())
        except Exception as e:
            pytest.fail(f"健康检查失败: {e}")
    
    def test_session_check_runs(self):
        """测试会话检查可以运行"""
        class Args:
            json = False
            detail = False
            predict = False
        
        try:
            ld.cmd_session(Args())
        except Exception as e:
            pytest.fail(f"会话检查失败: {e}")


class TestUtilityFunctions:
    """工具函数测试"""
    
    def test_fmt_tokens_large_number(self):
        """测试 token 格式化（大数字）"""
        result = ld.fmt_tokens(1_500_000)
        assert "M" in result, "大于1M的数字应显示M"
    
    def test_fmt_tokens_medium_number(self):
        """测试 token 格式化（中等数字）"""
        result = ld.fmt_tokens(50_000)
        assert "K" in result, "大于1K的数字应显示K"
    
    def test_fmt_tokens_small_number(self):
        """测试 token 格式化（小数字）"""
        result = ld.fmt_tokens(500)
        assert result == "500", "小于1K的数字应直接显示"
    
    def test_fmt_size_bytes(self):
        """测试大小格式化（字节）"""
        result = ld.fmt_size(500)
        assert "B" in result
    
    def test_fmt_size_kilobytes(self):
        """测试大小格式化（KB）"""
        result = ld.fmt_size(5000)
        assert "KB" in result
    
    def test_fmt_size_megabytes(self):
        """测试大小格式化（MB）"""
        result = ld.fmt_size(5_000_000)
        assert "MB" in result


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v"])