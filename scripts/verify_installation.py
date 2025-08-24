#!/usr/bin/env python3
"""
Installation verification script for the AI Chatbot system.
Checks all critical dependencies and provides a comprehensive status report.
"""

import sys
import importlib
import subprocess
from typing import Dict, List, Tuple

def test_import(module_name: str, package_name: str = None) -> Tuple[bool, str]:
    """Test if a module can be imported successfully."""
    try:
        if package_name:
            imported = importlib.import_module(module_name)
            # Try to get version if available
            version = getattr(imported, '__version__', 'unknown')
            return True, f"{package_name}: {version}"
        else:
            importlib.import_module(module_name)
            return True, f"{module_name}: OK"
    except ImportError as e:
        return False, f"{module_name}: FAILED - {str(e)}"
    except Exception as e:
        return False, f"{module_name}: ERROR - {str(e)}"

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version >= (3, 8):
        return True, f"Python {version.major}.{version.minor}.{version.micro}: OK"
    else:
        return False, f"Python {version.major}.{version.minor}.{version.micro}: TOO OLD (requires 3.8+)"

def main():
    """Run comprehensive installation verification."""
    print("🔍 AI Chatbot System - Installation Verification")
    print("=" * 50)
    
    # Check Python version
    python_ok, python_msg = check_python_version()
    print(f"🐍 {python_msg}")
    
    if not python_ok:
        print("❌ Python version incompatible. Please upgrade to Python 3.8+")
        sys.exit(1)
    
    # Critical packages to test
    critical_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("pydantic_settings", "Pydantic Settings"),
        ("sqlalchemy", "SQLAlchemy"),
        ("alembic", "Alembic"),
        ("requests", "Requests"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("flet", "Flet"),
        ("jose", "Python Jose"),
        ("passlib", "Passlib"),
        ("dotenv", "Python Dotenv"),
        ("click", "Click"),
        ("rich", "Rich"),
        ("typer", "Typer"),
    ]
    
    # Optional packages
    optional_packages = [
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("langchain", "LangChain"),
        ("chromadb", "ChromaDB"),
        ("tiktoken", "TikToken"),
    ]
    
    print("\n📦 Critical Packages:")
    print("-" * 30)
    
    critical_failed = []
    for module, name in critical_packages:
        success, msg = test_import(module, name)
        status = "✅" if success else "❌"
        print(f"{status} {msg}")
        if not success:
            critical_failed.append(name)
    
    print("\n📦 Optional Packages:")
    print("-" * 30)
    
    optional_failed = []
    for module, name in optional_packages:
        success, msg = test_import(module, name)
        status = "✅" if success else "⚠️"
        print(f"{status} {msg}")
        if not success:
            optional_failed.append(name)
    
    # Summary
    print("\n📊 Installation Summary:")
    print("=" * 50)
    
    if not critical_failed:
        print("✅ All critical packages installed successfully!")
        print("🚀 System is ready for development and testing.")
    else:
        print(f"❌ {len(critical_failed)} critical packages failed:")
        for package in critical_failed:
            print(f"   - {package}")
        print("\n🔧 Please run: pip install -r requirements.txt")
    
    if optional_failed:
        print(f"\n⚠️  {len(optional_failed)} optional packages not available:")
        for package in optional_failed:
            print(f"   - {package}")
        print("   These are optional for basic functionality.")
    
    # Test basic functionality
    print("\n🧪 Basic Functionality Tests:")
    print("-" * 30)
    
    try:
        # Test FastAPI import and basic setup
        from fastapi import FastAPI
        app = FastAPI()
        print("✅ FastAPI: Basic setup works")
        
        # Test Pydantic models
        from pydantic import BaseModel
        class TestModel(BaseModel):
            name: str
            age: int
        
        model = TestModel(name="test", age=25)
        print("✅ Pydantic: Model creation works")
        
        # Test SQLAlchemy
        from sqlalchemy import create_engine
        engine = create_engine("sqlite:///:memory:")
        print("✅ SQLAlchemy: Engine creation works")
        
        print("\n🎉 Installation verification completed successfully!")
        
        if not critical_failed:
            return 0  # Success
        else:
            return 1  # Critical failures
            
    except Exception as e:
        print(f"❌ Basic functionality test failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())