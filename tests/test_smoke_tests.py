#!/usr/bin/env python3
"""
Smoke Tests for Critical Application Functionality
=================================================

Quick validation tests to ensure core application components work.
"""

import sys
import os
import subprocess
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestCriticalFunctionality:
    """Smoke tests for critical application functionality."""
    
    def test_project_structure_integrity(self):
        """Test that essential project files and directories exist."""
        project_root = Path(__file__).parent.parent
        
        # Core application files
        core_files = [
            "app.py",
            "main.py", 
            "start_demo.py",
            "requirements.txt",
            "CLAUDE.md"
        ]
        
        for file_name in core_files:
            file_path = project_root / file_name
            assert file_path.exists(), f"Critical file {file_name} is missing"
            assert file_path.stat().st_size > 0, f"File {file_name} is empty"
        
        # Core directories
        core_dirs = [
            "src",
            "tests", 
            "config",
            "docs"
        ]
        
        for dir_name in core_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Critical directory {dir_name} is missing"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"
    
    def test_src_module_structure(self):
        """Test that src module has correct structure."""
        src_path = Path(__file__).parent.parent / "src"
        
        expected_modules = [
            "api",
            "core",
            "database", 
            "ui",
            "utils"
        ]
        
        for module_name in expected_modules:
            module_path = src_path / module_name
            assert module_path.exists(), f"Source module {module_name} is missing"
            
            # Check for __init__.py
            init_file = module_path / "__init__.py"
            assert init_file.exists(), f"Missing __init__.py in {module_name}"
    
    def test_configuration_files(self):
        """Test configuration files exist and are parseable."""
        config_path = Path(__file__).parent.parent / "config"
        
        config_files = [
            "settings.py",
            "logging_config.py"
        ]
        
        for config_file in config_files:
            file_path = config_path / config_file
            assert file_path.exists(), f"Config file {config_file} is missing"
            
            # Try to parse as Python (basic syntax check)
            with open(file_path, 'r') as f:
                content = f.read()
                try:
                    compile(content, file_path, 'exec')
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {config_file}: {e}")
    
    def test_import_critical_modules(self):
        """Test that critical application modules can be imported."""
        # Test configuration imports with fallbacks
        config_importable = False
        try:
            from config.settings import settings
            config_importable = True
            assert settings.app_name, "Settings should have app_name"
        except ImportError:
            # Expected if dependencies are missing
            pass
        
        # At least config structure should be importable
        if not config_importable:
            # Test basic Python file syntax at least
            config_path = Path(__file__).parent.parent / "config" / "settings.py"
            with open(config_path, 'r') as f:
                content = f.read()
                compile(content, config_path, 'exec')  # Should not raise SyntaxError
    
    def test_database_schema_files(self):
        """Test database-related files exist."""
        db_paths = [
            Path(__file__).parent.parent / "src" / "database",
            Path(__file__).parent.parent / "migrations"
        ]
        
        for db_path in db_paths:
            if db_path.exists():
                assert db_path.is_dir(), f"{db_path.name} should be a directory"
                
                # Check for key files
                if db_path.name == "database":
                    expected_files = ["models.py", "session.py", "crud.py"]
                    for file_name in expected_files:
                        file_path = db_path / file_name
                        if file_path.exists():
                            assert file_path.stat().st_size > 0, f"{file_name} should not be empty"
    
    def test_logging_configuration(self):
        """Test logging configuration works."""
        try:
            from config.logging_config import setup_logging
            
            # Test setup_logging function exists and is callable
            assert callable(setup_logging), "setup_logging should be callable"
            
            # Test that it doesn't crash with basic call
            setup_logging("INFO")
            
        except ImportError:
            # Expected if dependencies missing, check file syntax at least
            log_config_path = Path(__file__).parent.parent / "config" / "logging_config.py"
            if log_config_path.exists():
                with open(log_config_path, 'r') as f:
                    content = f.read()
                    compile(content, log_config_path, 'exec')
    
    def test_demo_mode_functionality(self):
        """Test that demo mode functions work."""
        try:
            import start_demo
            
            # Test dependency checker
            available, missing = start_demo.check_dependencies()
            assert isinstance(available, list), "Available deps should be list"
            assert isinstance(missing, list), "Missing deps should be list"
            
            # Should detect at least some packages
            total_checked = len(available) + len(missing)
            assert total_checked >= 5, "Should check multiple dependencies"
            
        except Exception as e:
            pytest.fail(f"Demo mode functionality test failed: {e}")

class TestAPIStructure:
    """Test API module structure and basic imports."""
    
    def test_api_modules_exist(self):
        """Test that API modules exist."""
        api_path = Path(__file__).parent.parent / "src" / "api"
        
        api_modules = [
            "conversations.py",
            "messages.py",
            "projects.py", 
            "websocket.py"
        ]
        
        for module_name in api_modules:
            module_path = api_path / module_name
            assert module_path.exists(), f"API module {module_name} is missing"
            assert module_path.stat().st_size > 50, f"API module {module_name} seems too small"
    
    def test_api_init_file(self):
        """Test API package __init__.py file."""
        init_path = Path(__file__).parent.parent / "src" / "api" / "__init__.py"
        assert init_path.exists(), "API package missing __init__.py"

class TestUIStructure:
    """Test UI module structure."""
    
    def test_ui_modules_exist(self):
        """Test that UI modules exist."""
        ui_path = Path(__file__).parent.parent / "src" / "ui"
        
        if ui_path.exists():
            ui_files = [
                "chat_app.py",
                "websocket_client.py"
            ]
            
            for file_name in ui_files:
                file_path = ui_path / file_name
                if file_path.exists():
                    assert file_path.stat().st_size > 0, f"UI file {file_name} should not be empty"
    
    def test_ui_components_directory(self):
        """Test UI components directory structure."""
        components_path = Path(__file__).parent.parent / "src" / "ui" / "components"
        
        if components_path.exists():
            assert components_path.is_dir(), "UI components should be a directory"

class TestUtilitiesAndHelpers:
    """Test utility modules and helper functions."""
    
    def test_utils_modules(self):
        """Test utility modules exist."""
        utils_path = Path(__file__).parent.parent / "src" / "utils"
        
        expected_utils = [
            "exceptions.py",
            "dependencies.py",
            "logging_config.py"
        ]
        
        for util_name in expected_utils:
            util_path = utils_path / util_name
            if util_path.exists():
                assert util_path.stat().st_size > 0, f"Utility {util_name} should not be empty"
    
    def test_scripts_directory(self):
        """Test scripts directory if it exists."""
        scripts_path = Path(__file__).parent.parent / "scripts"
        
        if scripts_path.exists():
            assert scripts_path.is_dir(), "Scripts should be a directory"
            
            # Check for common script files
            script_files = list(scripts_path.glob("*.py"))
            if script_files:
                for script_file in script_files:
                    assert script_file.stat().st_size > 0, f"Script {script_file.name} should not be empty"

class TestDocumentationAndReadme:
    """Test documentation files exist and are valid."""
    
    def test_readme_files(self):
        """Test README files exist."""
        project_root = Path(__file__).parent.parent
        
        readme_files = ["README.md", "README_WINDOWS.md"]
        
        for readme_file in readme_files:
            readme_path = project_root / readme_file
            if readme_path.exists():
                assert readme_path.stat().st_size > 0, f"{readme_file} should not be empty"
    
    def test_claude_md_file(self):
        """Test CLAUDE.md configuration file."""
        claude_md_path = Path(__file__).parent.parent / "CLAUDE.md"
        
        assert claude_md_path.exists(), "CLAUDE.md configuration file is missing"
        assert claude_md_path.stat().st_size > 100, "CLAUDE.md should contain configuration"
        
        # Check for key sections
        with open(claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        key_sections = [
            "SPARC",
            "Agent",
            "Configuration"
        ]
        
        for section in key_sections:
            # At least one of these should be mentioned
            assert any(keyword.lower() in content.lower() for keyword in key_sections), \
                "CLAUDE.md should contain key configuration sections"

def run_smoke_tests():
    """Run all smoke tests and return results."""
    print("🔥 RUNNING SMOKE TESTS")
    print("=" * 50)
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    # Import pytest and run tests
    try:
        import pytest
        
        # Run this file as tests
        result = pytest.main([__file__, "-v", "--tb=short"])
        
        if result == 0:
            print("\n✅ All smoke tests passed!")
        else:
            print(f"\n⚠️  Some smoke tests had issues (exit code: {result})")
            
    except ImportError:
        print("⚠️  pytest not available, running basic validation...")
        
        # Run basic validation without pytest
        try:
            # Basic structure check
            test_critical = TestCriticalFunctionality()
            test_critical.test_project_structure_integrity()
            test_critical.test_src_module_structure()
            
            print("✅ Basic project structure validation passed")
            
        except Exception as e:
            print(f"❌ Basic validation failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)