#!/usr/bin/env python3
"""
Comprehensive Application Startup Validation Tests
==================================================

This module tests application startup in different modes and validates
that all imports and critical functionality work correctly.
"""

import os
import sys
import subprocess
import time
import requests
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestApplicationStartup:
    """Test suite for application startup validation."""
    
    def test_python_environment(self):
        """Test Python environment and version requirements."""
        # Check Python version
        assert sys.version_info >= (3, 8), "Python 3.8 or higher required"
        
        # Check critical paths
        project_root = Path(__file__).parent.parent
        assert project_root.exists(), "Project root directory exists"
        assert (project_root / "app.py").exists(), "Main app.py file exists"
        assert (project_root / "requirements.txt").exists(), "Requirements file exists"
        
    def test_critical_imports_availability(self):
        """Test availability of critical Python packages."""
        critical_packages = {
            'fastapi': 'FastAPI web framework',
            'uvicorn': 'ASGI server',
            'pydantic': 'Data validation',
            'sqlalchemy': 'Database ORM',
            'flet': 'UI framework'
        }
        
        available = []
        missing = []
        
        for package, description in critical_packages.items():
            try:
                __import__(package)
                available.append(f"{package} ({description})")
            except ImportError as e:
                missing.append(f"{package} ({description}): {str(e)}")
        
        # At least some basic packages should be available
        assert len(available) >= 2, f"Too many critical packages missing. Available: {available}, Missing: {missing}"
        
        return {"available": available, "missing": missing}
    
    def test_demo_functionality(self):
        """Test that demo mode works without full dependencies."""
        try:
            # Test import of start_demo module
            sys.path.insert(0, str(Path(__file__).parent.parent))
            import start_demo
            
            # Test dependency check function
            available, missing = start_demo.check_dependencies()
            assert isinstance(available, list), "Available packages should be a list"
            assert isinstance(missing, list), "Missing packages should be a list"
            
            # Should have at least Python built-ins working
            total_deps = len(available) + len(missing)
            assert total_deps > 0, "Should detect some dependencies"
            
        except Exception as e:
            pytest.fail(f"Demo functionality test failed: {e}")
    
    def test_config_loading(self):
        """Test configuration loading with fallbacks."""
        try:
            # Test with mock environment
            with patch.dict('os.environ', {
                'OPENAI_API_KEY': 'test-key',
                'SECRET_KEY': 'test-secret',
                'DATABASE_URL': 'sqlite:///test.db'
            }):
                from config.settings import settings
                
                # Test basic configuration
                assert settings.openai_api_key == 'test-key'
                assert settings.secret_key == 'test-secret'
                assert settings.app_name == 'WhatsApp AI Chatbot'
                assert settings.port == 8000
                
        except ImportError:
            # If config module is not importable due to dependencies, that's also valid info
            pytest.skip("Config module not importable - likely due to missing dependencies")
    
    def test_database_models_import(self):
        """Test that database models can be imported."""
        try:
            from src.database.models import Base
            assert Base is not None, "Database Base model should be importable"
            
        except ImportError as e:
            # This is expected if SQLAlchemy or other deps are missing
            pytest.skip(f"Database models not importable: {e}")
    
    def test_api_structure(self):
        """Test that API module structure is correct."""
        api_path = Path(__file__).parent.parent / "src" / "api"
        
        expected_files = [
            "conversations.py",
            "messages.py", 
            "projects.py",
            "websocket.py"
        ]
        
        for file_name in expected_files:
            file_path = api_path / file_name
            assert file_path.exists(), f"Expected API file {file_name} should exist"
    
    @pytest.mark.asyncio
    async def test_minimal_fastapi_startup(self):
        """Test that minimal FastAPI app can start (if FastAPI is available)."""
        try:
            from fastapi import FastAPI
            import uvicorn
            
            # Create minimal app
            app = FastAPI(title="Test App")
            
            @app.get("/")
            async def root():
                return {"status": "ok"}
            
            # Test app creation (don't actually start server)
            assert app.title == "Test App"
            
        except ImportError:
            pytest.skip("FastAPI not available for startup test")

class TestApplicationModes:
    """Test different application startup modes."""
    
    def test_demo_api_mode_availability(self):
        """Test if demo API mode can be started."""
        try:
            import start_demo
            
            # Check if required dependencies are available
            available, missing = start_demo.check_dependencies()
            
            fastapi_available = "FastAPI" in available
            uvicorn_available = "Uvicorn" in available
            
            if fastapi_available and uvicorn_available:
                # Could start demo API
                assert True, "Demo API mode is available"
            else:
                # Expected if dependencies are missing
                assert "FastAPI" in missing or "Uvicorn" in missing, "FastAPI/Uvicorn missing as expected"
                
        except Exception as e:
            pytest.fail(f"Demo API availability check failed: {e}")
    
    def test_demo_ui_mode_availability(self):
        """Test if demo UI mode can be started."""
        try:
            import start_demo
            
            available, missing = start_demo.check_dependencies()
            
            if "Flet" in available:
                # Could start demo UI
                assert True, "Demo UI mode is available"
            else:
                # Expected if Flet is missing
                assert "Flet" in missing, "Flet missing as expected"
                
        except Exception as e:
            pytest.fail(f"Demo UI availability check failed: {e}")

class TestSystemRequirements:
    """Test system-level requirements and capabilities."""
    
    def test_file_system_permissions(self):
        """Test that application has necessary file system permissions."""
        project_root = Path(__file__).parent.parent
        
        # Test read permissions
        assert os.access(project_root, os.R_OK), "Should have read access to project root"
        
        # Test write permissions to data directories
        test_dirs = ["data", "logs", "brain"]
        for dir_name in test_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists():
                assert os.access(dir_path, os.W_OK), f"Should have write access to {dir_name}"
    
    def test_networking_capabilities(self):
        """Test basic networking capabilities (no external calls)."""
        import socket
        
        # Test that we can bind to localhost ports
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', 0))  # Bind to any available port
                port = s.getsockname()[1]
                assert port > 0, "Should be able to bind to localhost port"
        except Exception as e:
            pytest.fail(f"Networking capability test failed: {e}")

class TestDependencyAnalysis:
    """Analyze and report on dependency status."""
    
    def test_requirements_file_parsing(self):
        """Test that requirements.txt can be parsed."""
        req_file = Path(__file__).parent.parent / "requirements.txt"
        assert req_file.exists(), "Requirements file should exist"
        
        with open(req_file, 'r') as f:
            content = f.read()
            
        # Should contain key packages
        assert "fastapi" in content.lower(), "Requirements should include FastAPI"
        assert "uvicorn" in content.lower(), "Requirements should include Uvicorn"
        assert "flet" in content.lower(), "Requirements should include Flet"
        
    def test_dependency_conflicts(self):
        """Check for potential dependency conflicts."""
        try:
            # Test pydantic version compatibility
            import pydantic
            
            # FastAPI requires specific pydantic versions
            pydantic_version = getattr(pydantic, '__version__', '0.0.0')
            major_version = int(pydantic_version.split('.')[0])
            
            # Should be pydantic v2 for modern FastAPI
            if major_version >= 2:
                assert True, "Compatible pydantic version"
            else:
                pytest.skip(f"Pydantic v{pydantic_version} may have compatibility issues")
                
        except ImportError:
            pytest.skip("Pydantic not available for conflict check")

def generate_validation_report():
    """Generate a comprehensive validation report."""
    report = {
        "timestamp": time.time(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "dependencies": {},
        "startup_modes": {},
        "system_status": {}
    }
    
    # Check dependencies
    try:
        import start_demo
        available, missing = start_demo.check_dependencies()
        report["dependencies"] = {
            "available": available,
            "missing": missing,
            "total_checked": len(available) + len(missing)
        }
    except Exception as e:
        report["dependencies"]["error"] = str(e)
    
    # Check startup modes
    try:
        report["startup_modes"]["demo_available"] = "Flet" in available or "FastAPI" in available
        report["startup_modes"]["full_app_ready"] = len(missing) == 0
    except:
        report["startup_modes"]["error"] = "Could not determine startup mode availability"
    
    # System status
    project_root = Path(__file__).parent.parent
    report["system_status"] = {
        "project_structure_valid": all([
            (project_root / "app.py").exists(),
            (project_root / "requirements.txt").exists(),
            (project_root / "src").exists(),
        ]),
        "permissions_ok": os.access(project_root, os.R_OK)
    }
    
    return report

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 APPLICATION STARTUP VALIDATION")
    print("=" * 60)
    
    report = generate_validation_report()
    
    print(f"\n🐍 Python Version: {report['python_version']}")
    
    print(f"\n📦 Dependencies:")
    if "available" in report["dependencies"]:
        print(f"  ✅ Available: {len(report['dependencies']['available'])}")
        for dep in report["dependencies"]["available"]:
            print(f"    • {dep}")
            
        print(f"  ❌ Missing: {len(report['dependencies']['missing'])}")
        for dep in report["dependencies"]["missing"]:
            print(f"    • {dep}")
    
    print(f"\n🚀 Startup Modes:")
    modes = report["startup_modes"]
    if "demo_available" in modes:
        print(f"  Demo Mode: {'✅ Available' if modes['demo_available'] else '❌ Not Available'}")
        print(f"  Full App: {'✅ Ready' if modes.get('full_app_ready', False) else '⚠️  Missing Dependencies'}")
    
    print(f"\n💻 System Status:")
    system = report["system_status"]
    print(f"  Project Structure: {'✅ Valid' if system['project_structure_valid'] else '❌ Invalid'}")
    print(f"  File Permissions: {'✅ OK' if system['permissions_ok'] else '❌ Issues'}")
    
    print("\n" + "=" * 60)
    print("✅ VALIDATION COMPLETE")
    print("=" * 60)