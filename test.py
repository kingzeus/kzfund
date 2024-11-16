#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试运行器主程序
提供了自定义的测试结果格式化和测试运行器，支持彩色输出和详细的测试统计信息

Features:
    - 彩色输出支持 (通过colorama实现跨平台)
    - 详细的测试执行时间统计
    - 分类显示测试结果 (成功/失败/错误/跳过)
    - 美观的结果展示格式
    - 支持CI/CD环境的退出码

Usage:
    直接运行: python test.py
    指定测试模块: python test.py tests.test_datetime
"""

import os
import sys
import time
import unittest
from datetime import datetime
from typing import Dict, List

import colorama
from colorama import Fore, Style

# 初始化colorama以支持Windows下的彩色输出
colorama.init()

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class CustomTestResult(unittest.TestResult):
    """
    自定义测试结果格式化器

    继承自unittest.TestResult，添加了以下功能：
    - 测试执行时间统计
    - 彩色输出支持
    - 分类存储测试结果
    """

    def __init__(self):
        super().__init__()
        self.start_time = None
        # 用于存储不同类型的测试结果
        self.test_results: Dict[str, List[str]] = {
            "success": [],  # 成功的测试
            "failure": [],  # 失败的测试
            "error": [],  # 发生错误的测试
            "skipped": [],  # 跳过的测试
        }
        # 存储错误和失败的详细信息
        self.error_details: Dict[str, tuple] = {}
        self.failure_details: Dict[str, tuple] = {}

    def _format_test_result(self, test, status: str, color: str) -> str:
        """
        格式化单个测试结果

        Args:
            test: 测试用例对象
            status: 测试状态标识
            color: 输出颜色代码

        Returns:
            格式化后的测试结果字符串
        """
        elapsed = time.time() - self.start_time
        return f"{test.id():<60} {color}[{status}]{Style.RESET_ALL} ({elapsed:.3f}s)"

    def startTest(self, test):
        """记录测试开始时间"""
        self.start_time = time.time()
        super().startTest(test)

    def addSuccess(self, test):
        """记录成功的测试"""
        self.test_results["success"].append(self._format_test_result(test, "PASS", Fore.GREEN))
        super().addSuccess(test)

    def addError(self, test, err):
        """记录发生错误的测试"""
        self.test_results["error"].append(self._format_test_result(test, "ERROR", Fore.RED))
        self.error_details[test.id()] = err
        super().addError(test, err)

    def addFailure(self, test, err):
        """记录失败的测试"""
        self.test_results["failure"].append(self._format_test_result(test, "FAIL", Fore.RED))
        self.failure_details[test.id()] = err
        super().addFailure(test, err)

    def addSkip(self, test, reason):
        """记录跳过的测试"""
        self.test_results["skipped"].append(self._format_test_result(test, "SKIP", Fore.YELLOW))
        super().addSkip(test, reason)


class CustomTestRunner:
    """自定义测试运行器"""

    def __init__(self):
        self.start_time = None
        self.terminal_width = os.get_terminal_size().columns
        self.divider = "=" * self.terminal_width
        self.short_divider = "-" * self.terminal_width

    def _center_text(self, text: str) -> str:
        """居中显示文本"""
        return text.center(self.terminal_width)

    def _print_session_header(self):
        """打印测试会话头部信息"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{self.divider}")
        print(self._center_text(f"{Fore.CYAN}Test Session Started{Style.RESET_ALL}"))
        print(self._center_text(f"{Fore.CYAN}{current_time}{Style.RESET_ALL}"))
        print(f"{self.divider}\n")
        print(f"{Fore.CYAN}🚀 Running tests...{Style.RESET_ALL}\n")

    def _print_result_section(self, title: str, results: List[str], color: str = ""):
        """打印结果区块"""
        if results:
            icon = {
                "Successes": "✅",
                "Failures": "❌",
                "Errors": "⚠️",
                "Skipped": "⏭️",
            }.get(title, "")

            print(f"\n{self.short_divider}")
            if color:
                print(f"{color}{icon} {title} ({len(results)}){Style.RESET_ALL}")
            else:
                print(f"{icon} {title} ({len(results)})")
            print(f"{self.short_divider}")

            for result in results:
                print(result)

    def _print_statistics(self, result: CustomTestResult, time_taken: float):
        """打印统计信息"""
        total_tests = result.testsRun
        passed_tests = len(result.test_results["success"])
        failed_tests = len(result.failures)
        error_tests = len(result.errors)
        skipped_tests = len(result.skipped)

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n{self.divider}")
        print(self._center_text(f"{Fore.CYAN}Test Statistics{Style.RESET_ALL}"))
        print(self.divider)

        # 状态栏
        status = "PASSED" if failed_tests + error_tests == 0 else "FAILED"
        status_color = Fore.GREEN if status == "PASSED" else Fore.RED
        print(self._center_text(f"{status_color}{status}{Style.RESET_ALL}"))

        # 进度条
        bar_width = 50
        filled = int(success_rate / 100 * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"\nProgress: [{Fore.GREEN}{bar}{Style.RESET_ALL}] {success_rate:.1f}%\n")

        # 详细统计
        print(f"{'Total tests:':<20} {total_tests}")
        print(f"{Fore.GREEN}{'Passed:':<20} {passed_tests}{Style.RESET_ALL}")
        if failed_tests:
            print(f"{Fore.RED}{'Failed:':<20} {failed_tests}{Style.RESET_ALL}")
        if error_tests:
            print(f"{Fore.RED}{'Errors:':<20} {error_tests}{Style.RESET_ALL}")
        if skipped_tests:
            print(f"{Fore.YELLOW}{'Skipped:':<20} {skipped_tests}{Style.RESET_ALL}")
        print(f"{'Time taken:':<20} {time_taken:.2f}s")
        print(self.divider + "\n")

    def _format_error_detail(self, err_tuple) -> str:
        """格式化错误详情"""
        import traceback

        err_type, err_value, err_traceback = err_tuple
        # 获取格式化的追溯信息
        formatted_traceback = "".join(
            traceback.format_exception(err_type, err_value, err_traceback)
        )
        return formatted_traceback

    def _print_error_details(self, result: CustomTestResult):
        """打印错误和失败的详细信息"""
        if result.failures or result.errors:
            print(f"\n{self.divider}")
            print(self._center_text(f"{Fore.RED}Detailed Error Information{Style.RESET_ALL}"))
            print(self.divider)

            for test_id, failure in result.failure_details.items():
                print(f"\n{Fore.RED}❌ FAILURE in {test_id}{Style.RESET_ALL}")
                print(self.short_divider)
                print(self._format_error_detail(failure))

            for test_id, error in result.error_details.items():
                print(f"\n{Fore.RED}⚠️ ERROR in {test_id}{Style.RESET_ALL}")
                print(self.short_divider)
                print(self._format_error_detail(error))

    def run(self, test) -> CustomTestResult:
        """运行测试套件"""
        result = CustomTestResult()
        self.start_time = time.time()

        self._print_session_header()
        test(result)
        time_taken = time.time() - self.start_time

        # 打印测试结果摘要
        print(f"\n{self.divider}")
        print(self._center_text(f"{Fore.CYAN}Test Results Summary{Style.RESET_ALL}"))
        print(f"{self.divider}\n")

        # 按类别打印测试结果
        self._print_result_section("Successes", result.test_results["success"])
        self._print_result_section("Failures", result.test_results["failure"], Fore.RED)
        self._print_result_section("Errors", result.test_results["error"], Fore.RED)
        self._print_result_section("Skipped", result.test_results["skipped"], Fore.YELLOW)

        # 打印错误详情
        self._print_error_details(result)

        # 打印统计信息
        self._print_statistics(result, time_taken)

        return result


def run_tests() -> CustomTestResult:
    """运行所有测试用例"""
    # 发现并运行所有测试用例
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
    suite = loader.discover(start_dir, pattern="test_*.py")

    # 使用自定义的测试运行器
    runner = CustomTestRunner()
    return runner.run(suite)


if __name__ == "__main__":
    result = run_tests()
    # 如果有测试失败，使用非零退出码
    sys.exit(len(result.failures) + len(result.errors))
