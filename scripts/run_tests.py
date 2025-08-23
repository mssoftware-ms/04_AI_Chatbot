#!/usr/bin/env python3
"""
Test runner script for WhatsApp AI Chatbot project.

This script provides convenient commands for running different types of tests
with appropriate configurations and reporting.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], description: str) -> int:
    """Run a command and return its exit code."""
    print(f"\n🚀 {description}")
    print(f"📋 Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running command: {e}")
        return 1


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    try:
        import pytest
        import pytest_cov
        import pytest_asyncio
        print("✅ All testing dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing testing dependency: {e}")
        print("💡 Run: pip install -r requirements-test.txt")
        return False


def run_unit_tests(args) -> int:
    """Run unit tests with coverage."""
    cmd = [
        "pytest", 
        "tests/unit/",
        "-v",
        "--tb=short"
    ]
    
    if args.coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:tests/reports/coverage",
            "--cov-fail-under=80"
        ])
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    return run_command(cmd, "Running Unit Tests")


def run_integration_tests(args) -> int:
    """Run integration tests."""
    cmd = [
        "pytest",
        "tests/integration/",
        "-v",
        "--tb=short"
    ]
    
    if args.coverage:
        cmd.extend([
            "--cov=src",
            "--cov-append",
            "--cov-report=term-missing"
        ])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    return run_command(cmd, "Running Integration Tests")


def run_performance_tests(args) -> int:
    """Run performance tests and benchmarks."""
    cmd = [
        "pytest",
        "tests/performance/",
        "-v",
        "--tb=short",
        "--benchmark-json=tests/reports/benchmark.json"
    ]
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    return run_command(cmd, "Running Performance Tests")


def run_ui_tests(args) -> int:
    """Run UI component tests."""
    cmd = [
        "pytest",
        "tests/ui/",
        "-v",
        "--tb=short"
    ]
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    return run_command(cmd, "Running UI Tests")


def run_all_tests(args) -> int:
    """Run complete test suite."""
    cmd = [
        "pytest",
        "-v",
        "--tb=short",
        "--html=tests/reports/pytest_report.html",
        "--self-contained-html",
        "--junitxml=tests/reports/junit.xml"
    ]
    
    if args.coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:tests/reports/coverage",
            "--cov-report=xml:tests/reports/coverage.xml",
            "--cov-fail-under=80"
        ])
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    return run_command(cmd, "Running Complete Test Suite")


def run_fast_tests(args) -> int:
    """Run only fast tests (< 1 second)."""
    cmd = [
        "pytest",
        "-m", "fast",
        "-v",
        "--tb=short"
    ]
    
    if args.coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing"
        ])
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    return run_command(cmd, "Running Fast Tests Only")


def run_security_tests(args) -> int:
    """Run security-focused tests."""
    cmd = [
        "pytest",
        "-m", "security",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd, "Running Security Tests")


def lint_code(args) -> int:
    """Run code quality checks."""
    commands = [
        (["black", "--check", "--diff", "src/", "tests/"], "Black formatting check"),
        (["isort", "--check-only", "--diff", "src/", "tests/"], "Import sorting check"),
        (["flake8", "src/", "tests/", "--max-line-length=88"], "Linting check"),
        (["mypy", "src/", "--ignore-missing-imports"], "Type checking"),
        (["bandit", "-r", "src/", "-ll"], "Security linting")
    ]
    
    exit_code = 0
    for cmd, description in commands:
        result = run_command(cmd, description)
        if result != 0:
            exit_code = result
    
    return exit_code


def create_test_report(args) -> int:
    """Generate comprehensive test report."""
    print("\n📊 Generating comprehensive test report...")
    
    # Run tests with reporting
    cmd = [
        "pytest",
        "--html=tests/reports/comprehensive_report.html",
        "--self-contained-html",
        "--junitxml=tests/reports/junit.xml",
        "--cov=src",
        "--cov-report=html:tests/reports/coverage",
        "--cov-report=xml:tests/reports/coverage.xml",
        "-v"
    ]
    
    result = run_command(cmd, "Generating Test Reports")
    
    if result == 0:
        print("\n📊 Reports generated:")
        print("   📄 HTML Report: tests/reports/comprehensive_report.html")
        print("   📊 Coverage Report: tests/reports/coverage/index.html")
        print("   📋 JUnit XML: tests/reports/junit.xml")
    
    return result


def watch_tests(args) -> int:
    """Watch for file changes and run tests automatically."""
    try:
        import pytest_watch
    except ImportError:
        print("❌ pytest-watch not installed")
        print("💡 Run: pip install pytest-watch")
        return 1
    
    cmd = [
        "ptw",
        "--",
        "-v",
        "--tb=short"
    ]
    
    if args.test_type:
        cmd.extend([f"tests/{args.test_type}/"])
    
    return run_command(cmd, "Watching tests for file changes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test runner for WhatsApp AI Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_tests.py unit --coverage     # Unit tests with coverage
  python scripts/run_tests.py all --parallel      # All tests in parallel
  python scripts/run_tests.py fast                # Only fast tests
  python scripts/run_tests.py lint                # Code quality checks
  python scripts/run_tests.py watch --test-type unit  # Watch unit tests
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Test commands")
    
    # Unit tests
    unit_parser = subparsers.add_parser("unit", help="Run unit tests")
    unit_parser.add_argument("--coverage", action="store_true", help="Include coverage reporting")
    unit_parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    unit_parser.add_argument("--markers", help="Additional pytest markers")
    
    # Integration tests
    integration_parser = subparsers.add_parser("integration", help="Run integration tests")
    integration_parser.add_argument("--coverage", action="store_true", help="Include coverage reporting")
    integration_parser.add_argument("--markers", help="Additional pytest markers")
    
    # Performance tests
    performance_parser = subparsers.add_parser("performance", help="Run performance tests")
    performance_parser.add_argument("--markers", help="Additional pytest markers")
    
    # UI tests
    ui_parser = subparsers.add_parser("ui", help="Run UI tests")
    ui_parser.add_argument("--markers", help="Additional pytest markers")
    
    # All tests
    all_parser = subparsers.add_parser("all", help="Run all tests")
    all_parser.add_argument("--coverage", action="store_true", help="Include coverage reporting")
    all_parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    all_parser.add_argument("--markers", help="Additional pytest markers")
    
    # Fast tests
    fast_parser = subparsers.add_parser("fast", help="Run only fast tests")
    fast_parser.add_argument("--coverage", action="store_true", help="Include coverage reporting")
    fast_parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    
    # Security tests
    security_parser = subparsers.add_parser("security", help="Run security tests")
    
    # Code quality
    lint_parser = subparsers.add_parser("lint", help="Run code quality checks")
    
    # Test report
    report_parser = subparsers.add_parser("report", help="Generate comprehensive test report")
    
    # Watch tests
    watch_parser = subparsers.add_parser("watch", help="Watch for changes and run tests")
    watch_parser.add_argument("--test-type", choices=["unit", "integration", "ui"], help="Test type to watch")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Ensure reports directory exists
    reports_dir = Path("tests/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Route to appropriate function
    commands = {
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "performance": run_performance_tests,
        "ui": run_ui_tests,
        "all": run_all_tests,
        "fast": run_fast_tests,
        "security": run_security_tests,
        "lint": lint_code,
        "report": create_test_report,
        "watch": watch_tests
    }
    
    command_func = commands.get(args.command)
    if command_func:
        exit_code = command_func(args)
        
        if exit_code == 0:
            print(f"\n✅ {args.command.title()} completed successfully!")
        else:
            print(f"\n❌ {args.command.title()} failed with exit code {exit_code}")
        
        return exit_code
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())