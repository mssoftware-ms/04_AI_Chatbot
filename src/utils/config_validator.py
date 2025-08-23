"""
Configuration validation and environment setup utilities.

This module provides comprehensive configuration validation, environment variable
checking, and system readiness verification for the WhatsApp AI Chatbot.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import re

import openai
import requests
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    level: ValidationLevel
    component: str
    message: str
    fix_suggestion: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class ConfigValidator:
    """Comprehensive configuration validator for the application."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self._validation_rules = self._setup_validation_rules()
    
    def _setup_validation_rules(self) -> Dict[str, Any]:
        """Setup validation rules for different configuration aspects."""
        return {
            "required_env_vars": [
                "OPENAI_API_KEY",
                "SECRET_KEY"
            ],
            "optional_env_vars": [
                "GITHUB_TOKEN",
                "DATABASE_URL",
                "LOG_LEVEL",
                "ENVIRONMENT"
            ],
            "api_key_patterns": {
                "OPENAI_API_KEY": r"^sk-[a-zA-Z0-9]{48}$",
                "GITHUB_TOKEN": r"^ghp_[a-zA-Z0-9]{36}$"
            },
            "required_directories": [
                "./data",
                "./logs",
                "./brain/chroma",
                "./backups"
            ],
            "database_urls": {
                "sqlite": r"^sqlite(\+aiosqlite)?:///.*\.db$",
                "postgresql": r"^postgresql(\+asyncpg)?://.*",
                "mysql": r"^mysql(\+aiomysql)?://.*"
            },
            "port_ranges": {
                "api_port": (1024, 65535),
                "ui_port": (1024, 65535),
                "websocket_port": (1024, 65535)
            }
        }
    
    async def validate_environment(self) -> List[ValidationResult]:
        """Perform comprehensive environment validation."""
        self.results.clear()
        
        # Validate Python version
        await self._validate_python_version()
        
        # Validate environment variables
        await self._validate_environment_variables()
        
        # Validate API keys
        await self._validate_api_keys()
        
        # Validate directory structure
        await self._validate_directories()
        
        # Validate database configuration
        await self._validate_database_config()
        
        # Validate network ports
        await self._validate_network_ports()
        
        # Validate dependencies
        await self._validate_dependencies()
        
        # Validate file permissions
        await self._validate_file_permissions()
        
        return self.results
    
    async def _validate_python_version(self) -> None:
        """Validate Python version requirements."""
        min_version = (3, 9)
        current_version = sys.version_info[:2]
        
        if current_version < min_version:
            self.results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                component="python_version",
                message=f"Python {min_version[0]}.{min_version[1]}+ required, found {current_version[0]}.{current_version[1]}",
                fix_suggestion="Upgrade Python to version 3.9 or higher"
            ))
        else:
            self.results.append(ValidationResult(
                level=ValidationLevel.INFO,
                component="python_version",
                message=f"Python version {current_version[0]}.{current_version[1]} is compatible"
            ))
    
    async def _validate_environment_variables(self) -> None:
        """Validate required and optional environment variables."""
        # Check required variables
        for var in self._validation_rules["required_env_vars"]:
            value = os.getenv(var)
            if not value:
                self.results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    component="environment",
                    message=f"Required environment variable {var} is missing",
                    fix_suggestion=f"Set {var} in your .env file or environment"
                ))
            elif value.strip() == "":
                self.results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    component="environment",
                    message=f"Required environment variable {var} is empty",
                    fix_suggestion=f"Provide a valid value for {var}"
                ))
        
        # Check optional variables
        for var in self._validation_rules["optional_env_vars"]:
            value = os.getenv(var)
            if not value:
                self.results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    component="environment",
                    message=f"Optional environment variable {var} is not set",
                    fix_suggestion=f"Consider setting {var} for enhanced functionality"
                ))
    
    async def _validate_api_keys(self) -> None:
        """Validate API key formats and functionality."""
        for key_name, pattern in self._validation_rules["api_key_patterns"].items():
            key_value = os.getenv(key_name)
            
            if not key_value:
                continue  # Already handled in environment validation
            
            # Validate format
            if not re.match(pattern, key_value):
                self.results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    component="api_keys",
                    message=f"{key_name} format appears invalid",
                    fix_suggestion=f"Verify {key_name} follows expected format"
                ))
                continue
            
            # Test API key functionality
            if key_name == "OPENAI_API_KEY":
                await self._test_openai_key(key_value)
            elif key_name == "GITHUB_TOKEN":
                await self._test_github_token(key_value)
    
    async def _test_openai_key(self, api_key: str) -> None:
        """Test OpenAI API key functionality."""
        try:
            openai.api_key = api_key
            # Test with a simple model list request
            client = openai.OpenAI(api_key=api_key)
            models = client.models.list()
            
            self.results.append(ValidationResult(
                level=ValidationLevel.INFO,
                component="openai_api",
                message="OpenAI API key is valid and functional",
                details={"available_models": len(models.data)}
            ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                component="openai_api",
                message=f"OpenAI API key validation failed: {str(e)}",
                fix_suggestion="Verify your OpenAI API key and account status"
            ))
    
    async def _test_github_token(self, token: str) -> None:
        """Test GitHub token functionality."""
        try:
            headers = {"Authorization": f"token {token}"}
            response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_info = response.json()
                self.results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    component="github_api",
                    message="GitHub token is valid and functional",
                    details={"username": user_info.get("login")}
                ))
            else:
                self.results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    component="github_api",
                    message=f"GitHub token validation failed with status {response.status_code}",
                    fix_suggestion="Verify your GitHub token has appropriate permissions"
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                component="github_api",
                message=f"GitHub token test failed: {str(e)}",
                fix_suggestion="Check your internet connection and GitHub token"
            ))
    
    async def _validate_directories(self) -> None:
        """Validate required directory structure."""
        for dir_path in self._validation_rules["required_directories"]:
            path = Path(dir_path)
            
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self.results.append(ValidationResult(
                        level=ValidationLevel.INFO,
                        component="directories",
                        message=f"Created directory: {dir_path}"
                    ))
                except Exception as e:
                    self.results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        component="directories",
                        message=f"Cannot create directory {dir_path}: {str(e)}",
                        fix_suggestion=f"Ensure write permissions for {dir_path}"
                    ))
            elif not path.is_dir():
                self.results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    component="directories",
                    message=f"Path exists but is not a directory: {dir_path}",
                    fix_suggestion=f"Remove file at {dir_path} or choose different path"
                ))
            else:
                # Check write permissions
                if not os.access(path, os.W_OK):
                    self.results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        component="directories",
                        message=f"Directory not writable: {dir_path}",
                        fix_suggestion=f"Ensure write permissions for {dir_path}"
                    ))
    
    async def _validate_database_config(self) -> None:
        """Validate database configuration."""
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/chatbot.db")
        
        # Validate URL format
        valid_format = False
        for db_type, pattern in self._validation_rules["database_urls"].items():
            if re.match(pattern, db_url):
                valid_format = True
                self.results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    component="database",
                    message=f"Database URL format is valid ({db_type})"
                ))
                break
        
        if not valid_format:
            self.results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                component="database",
                message="Database URL format not recognized",
                fix_suggestion="Verify DATABASE_URL follows supported format"
            ))
        
        # For SQLite, check file path accessibility
        if "sqlite" in db_url:
            db_path = db_url.split("///")[-1]
            db_dir = Path(db_path).parent
            
            if not db_dir.exists():
                try:
                    db_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        component="database",
                        message=f"Cannot create database directory: {str(e)}",
                        fix_suggestion="Ensure write permissions for database directory"
                    ))
    
    async def _validate_network_ports(self) -> None:
        """Validate network port configurations."""
        port_configs = {
            "PORT": "api_port",
            "UI_PORT": "ui_port",
            "WS_PORT": "websocket_port"
        }
        
        used_ports = set()
        
        for env_var, port_type in port_configs.items():
            port_str = os.getenv(env_var)
            if not port_str:
                continue
            
            try:
                port = int(port_str)
                min_port, max_port = self._validation_rules["port_ranges"][port_type]
                
                if port < min_port or port > max_port:
                    self.results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        component="network",
                        message=f"Port {port} for {env_var} is outside recommended range {min_port}-{max_port}",
                        fix_suggestion=f"Use a port between {min_port} and {max_port}"
                    ))
                
                if port in used_ports:
                    self.results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        component="network",
                        message=f"Port {port} is configured for multiple services",
                        fix_suggestion="Use different ports for each service"
                    ))
                else:
                    used_ports.add(port)
                
            except ValueError:
                self.results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    component="network",
                    message=f"Invalid port number in {env_var}: {port_str}",
                    fix_suggestion="Use a valid integer port number"
                ))
    
    async def _validate_dependencies(self) -> None:
        """Validate critical dependencies are available."""
        critical_modules = [
            ("fastapi", "FastAPI web framework"),
            ("sqlalchemy", "Database ORM"),
            ("openai", "OpenAI API client"),
            ("chromadb", "Vector database"),
            ("flet", "UI framework")
        ]
        
        for module_name, description in critical_modules:
            try:
                __import__(module_name)
                self.results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    component="dependencies",
                    message=f"{description} is available"
                ))
            except ImportError:
                self.results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    component="dependencies",
                    message=f"Missing dependency: {module_name} ({description})",
                    fix_suggestion=f"Install {module_name} with: pip install {module_name}"
                ))
    
    async def _validate_file_permissions(self) -> None:
        """Validate file system permissions."""
        test_files = [
            "./test_write.tmp",
            "./data/test_write.tmp",
            "./logs/test_write.tmp"
        ]
        
        for test_file in test_files:
            test_path = Path(test_file)
            test_dir = test_path.parent
            
            if not test_dir.exists():
                continue  # Already handled in directory validation
            
            try:
                # Test write permission
                test_path.write_text("test")
                test_path.unlink()  # Clean up
                
            except Exception as e:
                self.results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    component="permissions",
                    message=f"Cannot write to {test_dir}: {str(e)}",
                    fix_suggestion=f"Ensure write permissions for {test_dir}"
                ))
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        summary = {
            "total_checks": len(self.results),
            "by_level": {level.value: 0 for level in ValidationLevel},
            "by_component": {},
            "critical_issues": [],
            "recommendations": []
        }
        
        for result in self.results:
            # Count by level
            summary["by_level"][result.level.value] += 1
            
            # Count by component
            if result.component not in summary["by_component"]:
                summary["by_component"][result.component] = 0
            summary["by_component"][result.component] += 1
            
            # Collect critical issues
            if result.level == ValidationLevel.CRITICAL:
                summary["critical_issues"].append(result.message)
            
            # Collect recommendations
            if result.fix_suggestion:
                summary["recommendations"].append({
                    "component": result.component,
                    "issue": result.message,
                    "fix": result.fix_suggestion
                })
        
        # Determine overall health
        error_count = summary["by_level"]["error"] + summary["by_level"]["critical"]
        if error_count == 0:
            summary["overall_status"] = "healthy"
        elif error_count <= 2:
            summary["overall_status"] = "warning"
        else:
            summary["overall_status"] = "critical"
        
        return summary
    
    def print_validation_report(self) -> None:
        """Print a formatted validation report to console."""
        summary = self.get_validation_summary()
        
        print("\n" + "="*60)
        print("🔍 CONFIGURATION VALIDATION REPORT")
        print("="*60)
        
        # Overall status
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "❌"
        }
        
        print(f"\n{status_emoji[summary['overall_status']]} Overall Status: {summary['overall_status'].upper()}")
        print(f"📊 Total Checks: {summary['total_checks']}")
        
        # Level breakdown
        print(f"\n📈 Results by Level:")
        for level, count in summary["by_level"].items():
            if count > 0:
                emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}
                print(f"  {emoji.get(level, '•')} {level.upper()}: {count}")
        
        # Critical issues
        if summary["critical_issues"]:
            print(f"\n🚨 Critical Issues:")
            for issue in summary["critical_issues"]:
                print(f"  • {issue}")
        
        # Recommendations
        if summary["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in summary["recommendations"][:5]:  # Show top 5
                print(f"  • {rec['component']}: {rec['fix']}")
        
        print("\n" + "="*60)


async def validate_configuration() -> ConfigValidator:
    """
    Perform comprehensive configuration validation.
    
    Returns:
        ConfigValidator: Validator instance with results
    """
    validator = ConfigValidator()
    await validator.validate_environment()
    return validator


def quick_validation_check() -> bool:
    """
    Perform a quick validation check for critical requirements.
    
    Returns:
        bool: True if basic requirements are met
    """
    required_vars = ["OPENAI_API_KEY", "SECRET_KEY"]
    
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"Missing critical environment variable: {var}")
            return False
    
    return True


if __name__ == "__main__":
    async def main():
        validator = await validate_configuration()
        validator.print_validation_report()
    
    asyncio.run(main())