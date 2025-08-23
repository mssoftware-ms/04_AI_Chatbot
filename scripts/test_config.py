#!/usr/bin/env python3
"""
Configuration Testing Script

This script comprehensively tests the application configuration to ensure:
1. Settings can be imported and instantiated correctly
2. All required directories are created
3. Default values work properly
4. Configuration works with and without .env file
5. All validators function correctly
6. Configuration issues are caught early

Usage:
    python scripts/test_config.py
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import traceback

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

class ConfigTester:
    """Comprehensive configuration testing suite."""
    
    def __init__(self):
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.temp_dir: Path = None
        self.original_cwd: str = os.getcwd()
        self.backup_env: Dict[str, str] = {}
        
    def setup_test_environment(self):
        """Set up isolated test environment."""
        print("🔧 Setting up test environment...")
        
        # Create temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp(prefix="config_test_"))
        print(f"   Created temp directory: {self.temp_dir}")
        
        # Backup current environment variables
        config_env_vars = [
            "APP_NAME", "DEBUG", "ENVIRONMENT", "HOST", "PORT", 
            "DATABASE_URL", "SECRET_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"
        ]
        
        for var in config_env_vars:
            if var in os.environ:
                self.backup_env[var] = os.environ[var]
                del os.environ[var]
        
        print("   Backed up and cleared environment variables")
        
    def cleanup_test_environment(self):
        """Clean up test environment."""
        print("🧹 Cleaning up test environment...")
        
        # Restore environment variables
        for var, value in self.backup_env.items():
            os.environ[var] = value
        
        # Change back to original directory
        os.chdir(self.original_cwd)
        
        # Remove temporary directory
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"   Removed temp directory: {self.temp_dir}")
            
    def test_basic_import(self) -> bool:
        """Test 1: Basic import and instantiation of Settings."""
        test_name = "basic_import"
        print("\n📦 Test 1: Basic Import and Instantiation")
        
        try:
            from config.config import Settings
            settings = Settings()
            
            self.test_results[test_name] = {
                "status": "PASS",
                "message": "Settings imported and instantiated successfully",
                "details": {
                    "app_name": settings.app_name,
                    "app_version": settings.app_version,
                    "environment": settings.environment,
                    "debug": settings.debug
                }
            }
            print("   ✅ Settings imported and instantiated successfully")
            print(f"   📋 App: {settings.app_name} v{settings.app_version}")
            print(f"   🔧 Environment: {settings.environment} (Debug: {settings.debug})")
            return True
            
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Failed to import or instantiate Settings: {str(e)}",
                "error": traceback.format_exc()
            }
            print(f"   ❌ Failed: {str(e)}")
            return False
    
    def test_directory_creation(self) -> bool:
        """Test 2: Directory creation functionality."""
        test_name = "directory_creation"
        print("\n📁 Test 2: Directory Creation")
        
        try:
            # Change to temp directory for testing
            os.chdir(self.temp_dir)
            
            from config.config import Settings
            settings = Settings()
            
            # Call create_directories method
            settings.create_directories()
            
            # Check if directories were created
            expected_dirs = [
                settings.upload_dir,
                settings.default_project_dir,
                settings.chroma_persist_directory,
                Path(settings.log_file).parent,
                Path(settings.database_url.replace("sqlite:///", "")).parent,
            ]
            
            created_dirs = []
            missing_dirs = []
            
            for directory in expected_dirs:
                dir_path = Path(directory)
                if dir_path.exists() and dir_path.is_dir():
                    created_dirs.append(str(dir_path))
                else:
                    missing_dirs.append(str(dir_path))
            
            if not missing_dirs:
                self.test_results[test_name] = {
                    "status": "PASS",
                    "message": "All required directories created successfully",
                    "details": {
                        "created_directories": created_dirs,
                        "directory_count": len(created_dirs)
                    }
                }
                print(f"   ✅ All {len(created_dirs)} directories created successfully")
                for dir_path in created_dirs:
                    print(f"      📂 {dir_path}")
                return True
            else:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "message": "Some directories were not created",
                    "details": {
                        "created_directories": created_dirs,
                        "missing_directories": missing_dirs
                    }
                }
                print(f"   ❌ Missing directories: {missing_dirs}")
                return False
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Directory creation failed: {str(e)}",
                "error": traceback.format_exc()
            }
            print(f"   ❌ Failed: {str(e)}")
            return False
    
    def test_default_values(self) -> bool:
        """Test 3: Default values work correctly."""
        test_name = "default_values"
        print("\n⚙️  Test 3: Default Values")
        
        try:
            from config.config import Settings
            settings = Settings()
            
            # Define expected default values
            expected_defaults = {
                "app_name": "WhatsApp AI Chatbot",
                "app_version": "1.0.0",
                "debug": False,
                "environment": "production",
                "host": "0.0.0.0",
                "port": 8000,
                "database_url": "sqlite:///./data/chatbot.db",
                "default_ai_model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.7,
                "algorithm": "HS256",
                "max_file_size": 10485760,
                "log_level": "INFO",
                "rate_limit_requests": 100,
                "enable_ai_chat": True,
            }
            
            correct_defaults = []
            incorrect_defaults = []
            
            for field, expected_value in expected_defaults.items():
                actual_value = getattr(settings, field)
                if actual_value == expected_value:
                    correct_defaults.append(f"{field}: {actual_value}")
                else:
                    incorrect_defaults.append(f"{field}: expected {expected_value}, got {actual_value}")
            
            if not incorrect_defaults:
                self.test_results[test_name] = {
                    "status": "PASS",
                    "message": "All default values are correct",
                    "details": {
                        "correct_defaults": correct_defaults,
                        "total_checked": len(expected_defaults)
                    }
                }
                print(f"   ✅ All {len(expected_defaults)} default values are correct")
                return True
            else:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "message": "Some default values are incorrect",
                    "details": {
                        "correct_defaults": correct_defaults,
                        "incorrect_defaults": incorrect_defaults
                    }
                }
                print(f"   ❌ Incorrect defaults: {incorrect_defaults}")
                return False
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Default values test failed: {str(e)}",
                "error": traceback.format_exc()
            }
            print(f"   ❌ Failed: {str(e)}")
            return False
    
    def test_without_env_file(self) -> bool:
        """Test 4: Configuration works without .env file."""
        test_name = "without_env_file"
        print("\n🚫 Test 4: Configuration Without .env File")
        
        try:
            # Change to temp directory (no .env file)
            os.chdir(self.temp_dir)
            
            from config.config import Settings
            settings = Settings()
            
            # Should use default values and not crash
            self.test_results[test_name] = {
                "status": "PASS",
                "message": "Configuration loads successfully without .env file",
                "details": {
                    "app_name": settings.app_name,
                    "environment": settings.environment,
                    "debug": settings.debug,
                    "port": settings.port
                }
            }
            print("   ✅ Configuration loads successfully without .env file")
            print(f"   📋 Using defaults: {settings.app_name}, env={settings.environment}")
            return True
            
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Configuration failed without .env file: {str(e)}",
                "error": traceback.format_exc()
            }
            print(f"   ❌ Failed: {str(e)}")
            return False
    
    def test_with_env_file(self) -> bool:
        """Test 5: Configuration works with .env file."""
        test_name = "with_env_file"
        print("\n📄 Test 5: Configuration With .env File")
        
        try:
            # Change to temp directory
            os.chdir(self.temp_dir)
            
            # Create test .env file
            env_content = """
# Test environment file
APP_NAME=Test Chatbot
DEBUG=true
ENVIRONMENT=testing
PORT=9000
SECRET_KEY=test_secret_key_123
DATABASE_URL=sqlite:///./test_data/test.db
MAX_TOKENS=1500
TEMPERATURE=0.8
LOG_LEVEL=DEBUG
ENABLE_AI_CHAT=false
"""
            
            with open(".env", "w") as f:
                f.write(env_content.strip())
            
            # Import settings (should pick up .env values)
            from config.config import Settings
            settings = Settings()
            
            # Verify .env values are loaded
            expected_values = {
                "app_name": "Test Chatbot",
                "debug": True,
                "environment": "testing",
                "port": 9000,
                "max_tokens": 1500,
                "temperature": 0.8,
                "log_level": "DEBUG",
                "enable_ai_chat": False
            }
            
            correct_env_values = []
            incorrect_env_values = []
            
            for field, expected_value in expected_values.items():
                actual_value = getattr(settings, field)
                if actual_value == expected_value:
                    correct_env_values.append(f"{field}: {actual_value}")
                else:
                    incorrect_env_values.append(f"{field}: expected {expected_value}, got {actual_value}")
            
            if not incorrect_env_values:
                self.test_results[test_name] = {
                    "status": "PASS",
                    "message": "Configuration loads successfully with .env file",
                    "details": {
                        "correct_env_values": correct_env_values,
                        "total_checked": len(expected_values)
                    }
                }
                print("   ✅ Configuration loads successfully with .env file")
                print(f"   📋 Loaded {len(expected_values)} values from .env")
                return True
            else:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "message": "Some .env values not loaded correctly",
                    "details": {
                        "correct_env_values": correct_env_values,
                        "incorrect_env_values": incorrect_env_values
                    }
                }
                print(f"   ❌ Incorrect env values: {incorrect_env_values}")
                return False
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Configuration with .env file failed: {str(e)}",
                "error": traceback.format_exc()
            }
            print(f"   ❌ Failed: {str(e)}")
            return False
    
    def test_validators(self) -> bool:
        """Test 6: Field validators work correctly."""
        test_name = "validators"
        print("\n✅ Test 6: Field Validators")
        
        try:
            # Change to temp directory
            os.chdir(self.temp_dir)
            
            # Test file extensions validator
            env_content = """
ALLOWED_FILE_EXTENSIONS=.txt,.pdf,.doc,.docx
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080","https://example.com"]
"""
            
            with open(".env", "w") as f:
                f.write(env_content.strip())
            
            from config.config import Settings
            settings = Settings()
            
            # Test file extensions parsing
            expected_extensions = ['.txt', '.pdf', '.doc', '.docx']
            if settings.allowed_file_extensions == expected_extensions:
                print("   ✅ File extensions validator works correctly")
                extensions_test = True
            else:
                print(f"   ❌ File extensions: expected {expected_extensions}, got {settings.allowed_file_extensions}")
                extensions_test = False
            
            # Test CORS origins parsing
            expected_origins = ['http://localhost:3000', 'http://localhost:8080', 'https://example.com']
            if settings.cors_origins == expected_origins:
                print("   ✅ CORS origins validator works correctly")
                cors_test = True
            else:
                print(f"   ❌ CORS origins: expected {expected_origins}, got {settings.cors_origins}")
                cors_test = False
            
            if extensions_test and cors_test:
                self.test_results[test_name] = {
                    "status": "PASS",
                    "message": "All validators work correctly",
                    "details": {
                        "file_extensions": settings.allowed_file_extensions,
                        "cors_origins": settings.cors_origins
                    }
                }
                return True
            else:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "message": "Some validators failed",
                    "details": {
                        "extensions_test": extensions_test,
                        "cors_test": cors_test
                    }
                }
                return False
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Validator tests failed: {str(e)}",
                "error": traceback.format_exc()
            }
            print(f"   ❌ Failed: {str(e)}")
            return False
    
    def test_secret_key_generation(self) -> bool:
        """Test 7: Secret key auto-generation and warning."""
        test_name = "secret_key_generation"
        print("\n🔒 Test 7: Secret Key Auto-Generation")
        
        try:
            # Change to temp directory
            os.chdir(self.temp_dir)
            
            # Test without SECRET_KEY (should auto-generate with warning)
            import warnings
            with warnings.catch_warnings(record=True) as warning_list:
                warnings.simplefilter("always")
                
                from config.config import Settings
                settings = Settings()
                
                # Check if warning was raised
                secret_warnings = [w for w in warning_list if "SECRET_KEY" in str(w.message)]
                
                if secret_warnings and settings.secret_key:
                    print("   ✅ Secret key auto-generation works with warning")
                    print(f"   🔑 Generated key length: {len(settings.secret_key)} characters")
                    
                    # Test with explicit SECRET_KEY
                    os.environ["SECRET_KEY"] = "test_explicit_secret_key_123"
                    
                    # Reload the module to pick up the environment variable
                    if 'config.config' in sys.modules:
                        del sys.modules['config.config']
                    
                    with warnings.catch_warnings(record=True) as warning_list2:
                        warnings.simplefilter("always")
                        from config.config import Settings
                        settings2 = Settings()
                        
                        # Should not have warnings when explicit key is provided
                        secret_warnings2 = [w for w in warning_list2 if "SECRET_KEY" in str(w.message)]
                        
                        if not secret_warnings2 and settings2.secret_key == "test_explicit_secret_key_123":
                            print("   ✅ Explicit secret key works without warning")
                            
                            self.test_results[test_name] = {
                                "status": "PASS",
                                "message": "Secret key auto-generation and explicit setting work correctly",
                                "details": {
                                    "auto_generated_length": len(settings.secret_key),
                                    "warning_raised": len(secret_warnings) > 0,
                                    "explicit_key_works": settings2.secret_key == "test_explicit_secret_key_123",
                                    "no_warning_with_explicit": len(secret_warnings2) == 0
                                }
                            }
                            return True
                        else:
                            print("   ❌ Explicit secret key handling failed")
                            return False
                else:
                    print("   ❌ Auto-generation failed or no warning raised")
                    return False
                    
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Secret key test failed: {str(e)}",
                "error": traceback.format_exc()
            }
            print(f"   ❌ Failed: {str(e)}")
            return False
    
    def print_configuration_status(self):
        """Print comprehensive configuration status."""
        print("\n" + "="*60)
        print("📊 CONFIGURATION STATUS REPORT")
        print("="*60)
        
        try:
            # Change back to project root to load actual config
            os.chdir(self.original_cwd)
            
            from config.config import Settings, settings
            
            print(f"\n📋 Application Information:")
            print(f"   App Name: {settings.app_name}")
            print(f"   Version: {settings.app_version}")
            print(f"   Environment: {settings.environment}")
            print(f"   Debug Mode: {settings.debug}")
            
            print(f"\n🌐 Server Configuration:")
            print(f"   Host: {settings.host}")
            print(f"   Port: {settings.port}")
            print(f"   Reload: {settings.reload}")
            
            print(f"\n🗄️  Database Configuration:")
            print(f"   Database URL: {settings.database_url}")
            print(f"   Echo SQL: {settings.database_echo}")
            
            print(f"\n🤖 AI Configuration:")
            print(f"   Default Model: {settings.default_ai_model}")
            print(f"   Max Tokens: {settings.max_tokens}")
            print(f"   Temperature: {settings.temperature}")
            print(f"   OpenAI Key Set: {'Yes' if settings.openai_api_key else 'No'}")
            print(f"   Anthropic Key Set: {'Yes' if settings.anthropic_api_key else 'No'}")
            
            print(f"\n📁 File & Directory Configuration:")
            print(f"   Upload Directory: {settings.upload_dir}")
            print(f"   Project Directory: {settings.default_project_dir}")
            print(f"   Chroma Directory: {settings.chroma_persist_directory}")
            print(f"   Log File: {settings.log_file}")
            print(f"   Max File Size: {settings.max_file_size / (1024*1024):.1f} MB")
            
            print(f"\n🔧 Feature Flags:")
            print(f"   AI Chat: {settings.enable_ai_chat}")
            print(f"   Project Management: {settings.enable_project_management}")
            print(f"   File Upload: {settings.enable_file_upload}")
            print(f"   Voice Messages: {settings.enable_voice_messages}")
            print(f"   Analytics: {settings.enable_analytics}")
            
            print(f"\n📝 Logging Configuration:")
            print(f"   Log Level: {settings.log_level}")
            print(f"   Max Log Size: {settings.log_max_size / (1024*1024):.1f} MB")
            print(f"   Backup Count: {settings.log_backup_count}")
            
            # Check directory status
            print(f"\n📂 Directory Status:")
            directories_to_check = [
                ("Upload Dir", settings.upload_dir),
                ("Project Dir", settings.default_project_dir),
                ("Chroma Dir", settings.chroma_persist_directory),
                ("Log Dir", Path(settings.log_file).parent),
                ("Data Dir", Path(settings.database_url.replace("sqlite:///", "")).parent),
            ]
            
            for name, path in directories_to_check:
                exists = Path(path).exists()
                status = "✅ EXISTS" if exists else "❌ MISSING"
                print(f"   {name}: {path} - {status}")
            
        except Exception as e:
            print(f"\n❌ Error loading configuration for status report: {str(e)}")
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 Results: {passed_tests}/{total_tests} tests passed")
        
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED! Configuration is working correctly.")
        else:
            print(f"⚠️  {failed_tests} test(s) failed. See details below:")
            
            for test_name, result in self.test_results.items():
                if result["status"] == "FAIL":
                    print(f"\n❌ {test_name.upper()}:")
                    print(f"   Message: {result['message']}")
                    if "error" in result:
                        error_lines = result['error'].split('\n') if result['error'] else []
                        error_msg = error_lines[-2] if len(error_lines) > 1 else (error_lines[0] if error_lines else 'Unknown')
                        print(f"   Error: {error_msg}")
        
        print("\n" + "="*60)
        
        return failed_tests == 0
    
    def run_all_tests(self) -> bool:
        """Run all configuration tests."""
        print("🚀 Starting Configuration Test Suite")
        print("="*60)
        
        try:
            self.setup_test_environment()
            
            # Run all tests
            tests = [
                self.test_basic_import,
                self.test_directory_creation,
                self.test_default_values,
                self.test_without_env_file,
                self.test_with_env_file,
                self.test_validators,
                self.test_secret_key_generation,
            ]
            
            for test in tests:
                try:
                    test()
                except Exception as e:
                    print(f"   💥 Unexpected error in test: {str(e)}")
            
            self.print_configuration_status()
            success = self.print_test_summary()
            
            return success
            
        finally:
            self.cleanup_test_environment()


def main():
    """Main entry point for configuration testing."""
    tester = ConfigTester()
    success = tester.run_all_tests()
    
    if success:
        print("✅ Configuration testing completed successfully!")
        sys.exit(0)
    else:
        print("❌ Configuration testing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()