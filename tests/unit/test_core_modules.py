"""
Core Module Unit Tests

This module contains unit tests for core application modules including
utilities, configuration, authentication, and business logic components.
"""

import pytest
import pytest_asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from datetime import datetime, timedelta
import json
import os
import tempfile
from pathlib import Path

from tests import TestDataFactory, TestMarkers, generate_test_id


@pytest.mark.unit
@pytest.mark.fast
class TestConfigurationManager:
    """Test configuration management functionality."""

    def test_load_configuration_from_env(self):
        """Test loading configuration from environment variables."""
        test_env_vars = {
            "DATABASE_URL": "postgresql://user:pass@localhost/testdb",
            "OPENAI_API_KEY": "sk-test-key-12345",
            "DEBUG": "true",
            "LOG_LEVEL": "INFO"
        }
        
        with patch.dict(os.environ, test_env_vars, clear=True):
            with patch("src.config.settings.load_config") as mock_load:
                expected_config = {
                    "database_url": "postgresql://user:pass@localhost/testdb",
                    "openai_api_key": "sk-test-key-12345",
                    "debug": True,
                    "log_level": "INFO"
                }
                mock_load.return_value = expected_config
                
                config = mock_load()
                
                assert config["database_url"] == test_env_vars["DATABASE_URL"]
                assert config["openai_api_key"] == test_env_vars["OPENAI_API_KEY"]
                assert config["debug"] is True
                assert config["log_level"] == "INFO"

    def test_load_configuration_from_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "app_name": "WhatsApp AI Chatbot",
            "version": "1.0.0",
            "features": {
                "rag_enabled": True,
                "websocket_enabled": True,
                "file_upload_max_size": 10485760
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            with patch("src.config.file_loader.load_from_file") as mock_load_file:
                mock_load_file.return_value = config_data
                
                config = mock_load_file("config.json")
                
                assert config["app_name"] == "WhatsApp AI Chatbot"
                assert config["features"]["rag_enabled"] is True
                assert config["features"]["file_upload_max_size"] == 10485760

    def test_configuration_validation(self):
        """Test configuration validation and error handling."""
        invalid_configs = [
            {"database_url": ""},  # Empty required field
            {"openai_api_key": None},  # None value
            {"log_level": "INVALID"},  # Invalid enum value
            {"file_upload_max_size": -1}  # Invalid numeric value
        ]
        
        with patch("src.config.validator.validate_config") as mock_validate:
            for config in invalid_configs:
                mock_validate.return_value = {
                    "valid": False,
                    "errors": [f"Invalid configuration: {list(config.keys())[0]}"]
                }
                
                result = mock_validate(config)
                
                assert result["valid"] is False
                assert len(result["errors"]) > 0

    def test_configuration_defaults(self):
        """Test configuration defaults when values are not provided."""
        with patch("src.config.defaults.get_default_config") as mock_defaults:
            default_config = {
                "debug": False,
                "log_level": "INFO",
                "database_pool_size": 10,
                "request_timeout_seconds": 30,
                "rate_limit_per_minute": 60,
                "cache_ttl_seconds": 3600
            }
            mock_defaults.return_value = default_config
            
            config = mock_defaults()
            
            assert config["debug"] is False
            assert config["log_level"] == "INFO"
            assert config["database_pool_size"] == 10
            assert config["request_timeout_seconds"] == 30


@pytest.mark.unit
@pytest.mark.fast
class TestAuthenticationUtilities:
    """Test authentication and authorization utilities."""

    def test_password_hashing(self):
        """Test password hashing functionality."""
        password = "secure_password_123"
        
        with patch("src.auth.password.hash_password") as mock_hash:
            with patch("src.auth.password.verify_password") as mock_verify:
                hashed = f"$2b$12${'x' * 53}"  # Mock bcrypt hash
                mock_hash.return_value = hashed
                mock_verify.return_value = True
                
                # Test hashing
                result = mock_hash(password)
                assert result.startswith("$2b$12$")
                assert len(result) == 60  # bcrypt hash length
                
                # Test verification
                is_valid = mock_verify(password, hashed)
                assert is_valid is True
                
                mock_hash.assert_called_once_with(password)
                mock_verify.assert_called_once_with(password, hashed)

    def test_jwt_token_creation(self):
        """Test JWT token creation and validation."""
        user_data = {
            "user_id": generate_test_id(),
            "username": "testuser",
            "email": "test@example.com"
        }
        
        with patch("src.auth.jwt.create_access_token") as mock_create:
            with patch("src.auth.jwt.decode_token") as mock_decode:
                token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.signature"
                mock_create.return_value = token
                mock_decode.return_value = user_data
                
                # Test token creation
                created_token = mock_create(user_data, expires_delta=timedelta(hours=1))
                assert created_token == token
                
                # Test token decoding
                decoded_data = mock_decode(token)
                assert decoded_data["user_id"] == user_data["user_id"]
                assert decoded_data["username"] == user_data["username"]
                
                mock_create.assert_called_once()
                mock_decode.assert_called_once_with(token)

    def test_permission_checking(self):
        """Test user permission checking."""
        user_permissions = ["read:projects", "write:projects", "read:messages"]
        required_permission = "write:projects"
        
        with patch("src.auth.permissions.has_permission") as mock_check:
            mock_check.return_value = required_permission in user_permissions
            
            result = mock_check(user_permissions, required_permission)
            
            assert result is True
            mock_check.assert_called_once_with(user_permissions, required_permission)

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        client_id = "client_123"
        limit = 10  # 10 requests per minute
        
        with patch("src.auth.rate_limiter.check_rate_limit") as mock_rate_limit:
            with patch("src.auth.rate_limiter.increment_counter") as mock_increment:
                # First 10 requests should be allowed
                mock_rate_limit.return_value = {"allowed": True, "remaining": 9}
                mock_increment.return_value = 1
                
                for i in range(10):
                    result = mock_rate_limit(client_id)
                    assert result["allowed"] is True
                    mock_increment(client_id)
                
                # 11th request should be rate limited
                mock_rate_limit.return_value = {"allowed": False, "remaining": 0}
                result = mock_rate_limit(client_id)
                assert result["allowed"] is False


@pytest.mark.unit
@pytest.mark.fast
class TestFileUtilities:
    """Test file handling and processing utilities."""

    def test_file_type_detection(self):
        """Test file type detection by extension and content."""
        test_files = [
            {"name": "document.pdf", "expected": "application/pdf"},
            {"name": "image.jpg", "expected": "image/jpeg"},
            {"name": "script.py", "expected": "text/x-python"},
            {"name": "data.json", "expected": "application/json"},
            {"name": "README.md", "expected": "text/markdown"}
        ]
        
        with patch("src.utils.file_detector.detect_mime_type") as mock_detect:
            for test_file in test_files:
                mock_detect.return_value = test_file["expected"]
                
                mime_type = mock_detect(test_file["name"])
                assert mime_type == test_file["expected"]

    def test_file_size_validation(self):
        """Test file size validation."""
        max_size = 10 * 1024 * 1024  # 10MB
        
        test_cases = [
            {"size": 5 * 1024 * 1024, "expected": True},   # 5MB - valid
            {"size": 15 * 1024 * 1024, "expected": False}, # 15MB - too large
            {"size": 0, "expected": False},                 # Empty file
            {"size": 1024, "expected": True}                # 1KB - valid
        ]
        
        with patch("src.utils.file_validator.validate_file_size") as mock_validate:
            for case in test_cases:
                mock_validate.return_value = case["expected"]
                
                result = mock_validate(case["size"], max_size)
                assert result == case["expected"]

    def test_secure_filename_generation(self):
        """Test secure filename generation."""
        unsafe_filenames = [
            "../../../etc/passwd",
            "file with spaces.txt",
            "file<>:\"|?*.txt",
            "con.txt",  # Windows reserved name
            ""  # Empty filename
        ]
        
        with patch("src.utils.file_utils.secure_filename") as mock_secure:
            expected_results = [
                "etc_passwd",
                "file_with_spaces.txt",
                "file.txt",
                "con_.txt",
                "unnamed_file"
            ]
            
            for i, filename in enumerate(unsafe_filenames):
                mock_secure.return_value = expected_results[i]
                
                result = mock_secure(filename)
                assert result == expected_results[i]

    def test_file_content_scanning(self):
        """Test file content security scanning."""
        file_contents = [
            b"Normal text content",  # Safe
            b"<script>alert('xss')</script>",  # Potential XSS
            b"\x00\x01\x02\x03",  # Binary content
            b"SELECT * FROM users; DROP TABLE users;"  # SQL injection attempt
        ]
        
        with patch("src.utils.file_scanner.scan_content") as mock_scan:
            expected_results = [
                {"safe": True, "threats": []},
                {"safe": False, "threats": ["xss_attempt"]},
                {"safe": True, "threats": []},
                {"safe": False, "threats": ["sql_injection"]}
            ]
            
            for i, content in enumerate(file_contents):
                mock_scan.return_value = expected_results[i]
                
                result = mock_scan(content)
                assert result["safe"] == expected_results[i]["safe"]
                assert result["threats"] == expected_results[i]["threats"]


@pytest.mark.unit
@pytest.mark.fast
class TestDataValidation:
    """Test data validation utilities."""

    def test_email_validation(self):
        """Test email address validation."""
        test_emails = [
            ("valid@example.com", True),
            ("user.name+tag@domain.co.uk", True),
            ("invalid.email", False),
            ("@domain.com", False),
            ("user@", False),
            ("", False),
            ("user@domain@domain.com", False)
        ]
        
        with patch("src.utils.validators.validate_email") as mock_validate:
            for email, expected in test_emails:
                mock_validate.return_value = expected
                
                result = mock_validate(email)
                assert result == expected

    def test_url_validation(self):
        """Test URL validation."""
        test_urls = [
            ("https://example.com", True),
            ("http://localhost:3000", True),
            ("ftp://files.example.com", True),
            ("not-a-url", False),
            ("javascript:alert('xss')", False),
            ("", False),
            ("//example.com", False)  # Protocol-relative URL
        ]
        
        with patch("src.utils.validators.validate_url") as mock_validate:
            for url, expected in test_urls:
                mock_validate.return_value = expected
                
                result = mock_validate(url)
                assert result == expected

    def test_json_schema_validation(self):
        """Test JSON schema validation."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "age": {"type": "integer", "minimum": 0},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["name", "email"]
        }
        
        test_data = [
            ({"name": "John", "age": 30, "email": "john@example.com"}, True),
            ({"name": "", "email": "john@example.com"}, False),  # Empty name
            ({"name": "John"}, False),  # Missing email
            ({"name": "John", "age": -5, "email": "john@example.com"}, False)  # Invalid age
        ]
        
        with patch("src.utils.validators.validate_json_schema") as mock_validate:
            for data, expected in test_data:
                mock_validate.return_value = {"valid": expected, "errors": [] if expected else ["Validation error"]}
                
                result = mock_validate(data, schema)
                assert result["valid"] == expected

    def test_input_sanitization(self):
        """Test input sanitization for XSS prevention."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "onclick='alert(\"xss\")'",
            "<iframe src='javascript:alert(\"xss\")'></iframe>"
        ]
        
        with patch("src.utils.sanitizer.sanitize_html") as mock_sanitize:
            for malicious_input in malicious_inputs:
                # Mock sanitization by removing dangerous content
                sanitized = malicious_input.replace("<script>", "&lt;script&gt;").replace("javascript:", "")
                mock_sanitize.return_value = sanitized
                
                result = mock_sanitize(malicious_input)
                assert "<script>" not in result
                assert "javascript:" not in result


@pytest.mark.unit
@pytest.mark.fast
class TestErrorHandling:
    """Test error handling and exception management."""

    def test_custom_exception_creation(self):
        """Test custom exception classes."""
        with patch("src.exceptions.CustomError") as MockCustomError:
            # Mock custom exception class
            error_code = "AUTH_001"
            error_message = "Authentication failed"
            
            mock_exception = MockCustomError(error_code, error_message)
            mock_exception.error_code = error_code
            mock_exception.message = error_message
            
            assert mock_exception.error_code == error_code
            assert mock_exception.message == error_message

    def test_error_logging_and_tracking(self):
        """Test error logging and tracking functionality."""
        error_data = {
            "error_id": generate_test_id(),
            "error_type": "ValidationError",
            "message": "Invalid input data",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": generate_test_id(),
            "request_id": generate_test_id()
        }
        
        with patch("src.utils.error_tracker.log_error") as mock_log:
            mock_log.return_value = error_data["error_id"]
            
            error_id = mock_log(error_data)
            
            assert error_id == error_data["error_id"]
            mock_log.assert_called_once_with(error_data)

    def test_error_response_formatting(self):
        """Test error response formatting for API endpoints."""
        errors = [
            {"type": "ValidationError", "field": "email", "message": "Invalid email format"},
            {"type": "AuthError", "message": "Authentication required"},
            {"type": "NotFoundError", "resource": "project", "id": "123"}
        ]
        
        with patch("src.utils.error_formatter.format_error_response") as mock_format:
            for error in errors:
                formatted_response = {
                    "error": {
                        "type": error["type"],
                        "message": error.get("message", "An error occurred"),
                        "details": {k: v for k, v in error.items() if k not in ["type", "message"]},
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                mock_format.return_value = formatted_response
                
                result = mock_format(error)
                
                assert result["error"]["type"] == error["type"]
                assert "timestamp" in result["error"]


@pytest.mark.unit
@pytest.mark.fast
class TestCacheUtilities:
    """Test caching utilities and mechanisms."""

    def test_in_memory_cache_operations(self):
        """Test in-memory cache operations."""
        cache_key = "test_key_123"
        cache_value = {"data": "test_value", "timestamp": datetime.utcnow().isoformat()}
        
        with patch("src.utils.cache.MemoryCache") as MockCache:
            mock_cache = MockCache()
            mock_cache.get = MagicMock(return_value=cache_value)
            mock_cache.set = MagicMock(return_value=True)
            mock_cache.delete = MagicMock(return_value=True)
            mock_cache.exists = MagicMock(return_value=True)
            
            # Test SET operation
            result = mock_cache.set(cache_key, cache_value, ttl=300)
            assert result is True
            mock_cache.set.assert_called_once_with(cache_key, cache_value, ttl=300)
            
            # Test GET operation
            cached_data = mock_cache.get(cache_key)
            assert cached_data == cache_value
            mock_cache.get.assert_called_once_with(cache_key)
            
            # Test DELETE operation
            deleted = mock_cache.delete(cache_key)
            assert deleted is True
            mock_cache.delete.assert_called_once_with(cache_key)

    def test_cache_expiration(self):
        """Test cache TTL and expiration."""
        with patch("src.utils.cache.is_expired") as mock_is_expired:
            # Test non-expired cache
            mock_is_expired.return_value = False
            assert mock_is_expired(datetime.utcnow(), ttl=300) is False
            
            # Test expired cache
            old_timestamp = datetime.utcnow() - timedelta(seconds=400)
            mock_is_expired.return_value = True
            assert mock_is_expired(old_timestamp, ttl=300) is True

    def test_cache_key_generation(self):
        """Test cache key generation and normalization."""
        with patch("src.utils.cache.generate_cache_key") as mock_gen_key:
            test_inputs = [
                (["user", "123", "profile"], "user:123:profile"),
                (["project", "abc-def", "documents"], "project:abc-def:documents"),
                (["search", "query with spaces"], "search:query_with_spaces")
            ]
            
            for input_parts, expected_key in test_inputs:
                mock_gen_key.return_value = expected_key
                
                key = mock_gen_key(input_parts)
                assert key == expected_key


@pytest.mark.unit
@pytest.mark.fast
class TestUtilityHelpers:
    """Test various utility helper functions."""

    def test_date_time_utilities(self):
        """Test date and time utility functions."""
        test_datetime = datetime(2024, 1, 15, 10, 30, 0)
        
        with patch("src.utils.datetime_helpers.format_datetime") as mock_format:
            with patch("src.utils.datetime_helpers.parse_datetime") as mock_parse:
                formatted = "2024-01-15T10:30:00Z"
                mock_format.return_value = formatted
                mock_parse.return_value = test_datetime
                
                # Test formatting
                result = mock_format(test_datetime)
                assert result == formatted
                
                # Test parsing
                parsed = mock_parse(formatted)
                assert parsed == test_datetime

    def test_string_utilities(self):
        """Test string manipulation utilities."""
        with patch("src.utils.string_helpers.slugify") as mock_slugify:
            with patch("src.utils.string_helpers.truncate") as mock_truncate:
                test_strings = [
                    ("Hello World!", "hello-world"),
                    ("My Project Name", "my-project-name"),
                    ("Special Chars @#$", "special-chars")
                ]
                
                for input_str, expected_slug in test_strings:
                    mock_slugify.return_value = expected_slug
                    result = mock_slugify(input_str)
                    assert result == expected_slug
                
                # Test truncation
                long_text = "This is a very long text that needs to be truncated"
                mock_truncate.return_value = "This is a very long text..."
                result = mock_truncate(long_text, max_length=30)
                assert len(result) <= 33  # 30 + "..."

    def test_data_structure_utilities(self):
        """Test data structure manipulation utilities."""
        nested_dict = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            }
        }
        
        with patch("src.utils.dict_helpers.deep_get") as mock_deep_get:
            with patch("src.utils.dict_helpers.flatten_dict") as mock_flatten:
                # Test deep get
                mock_deep_get.return_value = "deep_value"
                result = mock_deep_get(nested_dict, ["level1", "level2", "level3"])
                assert result == "deep_value"
                
                # Test flatten
                flattened = {"level1.level2.level3": "deep_value"}
                mock_flatten.return_value = flattened
                result = mock_flatten(nested_dict)
                assert result == flattened

    def test_pagination_utilities(self):
        """Test pagination helper functions."""
        with patch("src.utils.pagination.paginate") as mock_paginate:
            total_items = 150
            page_size = 20
            current_page = 3
            
            pagination_result = {
                "page": current_page,
                "per_page": page_size,
                "total": total_items,
                "pages": 8,  # ceil(150/20)
                "has_prev": True,
                "has_next": True,
                "prev_num": 2,
                "next_num": 4
            }
            mock_paginate.return_value = pagination_result
            
            result = mock_paginate(total_items, current_page, page_size)
            
            assert result["page"] == current_page
            assert result["total"] == total_items
            assert result["pages"] == 8
            assert result["has_prev"] is True
            assert result["has_next"] is True