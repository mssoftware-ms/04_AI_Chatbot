"""
Security utilities for input sanitization, validation, and protection.

This module provides comprehensive security measures including input sanitization,
rate limiting helpers, SQL injection prevention, and XSS protection.
"""

import re
import html
import logging
import hashlib
import secrets
from typing import Any, Dict, List, Optional, Union, Set
from urllib.parse import quote, unquote
from datetime import datetime, timedelta
import bleach
from functools import wraps

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Comprehensive input sanitization and validation."""
    
    # Common dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
        r"(['\";])",
        r"(--|\#|/\*|\*/)",
        r"(\bor\b\s+\d+\s*=\s*\d+)",
        r"(\band\b\s+\d+\s*=\s*\d+)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"<iframe[^>]*>.*?</iframe>",
        r"javascript:",
        r"on\w+\s*=",
        r"data:text/html",
    ]
    
    # Safe HTML tags and attributes
    ALLOWED_HTML_TAGS = [
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'ul', 'ol', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'
    ]
    
    ALLOWED_HTML_ATTRIBUTES = {
        '*': ['class'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
    }
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize input sanitizer.
        
        Args:
            strict_mode: Enable strict sanitization rules
        """
        self.strict_mode = strict_mode
        self._setup_patterns()
    
    def _setup_patterns(self) -> None:
        """Compile regex patterns for performance."""
        self.sql_pattern = re.compile(
            '|'.join(self.SQL_INJECTION_PATTERNS),
            re.IGNORECASE | re.DOTALL
        )
        
        self.xss_pattern = re.compile(
            '|'.join(self.XSS_PATTERNS),
            re.IGNORECASE | re.DOTALL
        )
    
    def sanitize_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text input for safe processing.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length].rstrip()
        
        # HTML escape for safety
        if self.strict_mode:
            text = html.escape(text)
        
        return text
    
    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content, allowing only safe tags.
        
        Args:
            html_content: HTML content to sanitize
            
        Returns:
            Sanitized HTML
        """
        return bleach.clean(
            html_content,
            tags=self.ALLOWED_HTML_TAGS,
            attributes=self.ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )
    
    def validate_phone_number(self, phone: str) -> Optional[str]:
        """
        Validate and normalize phone number.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Normalized phone number or None if invalid
        """
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Phone number patterns (international and local)
        patterns = [
            r'^\+\d{10,15}$',  # International format
            r'^\d{10,15}$',    # Without country code
        ]
        
        for pattern in patterns:
            if re.match(pattern, cleaned):
                return cleaned
        
        return None
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email to validate
            
        Returns:
            True if valid email format
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip().lower()))
    
    def check_sql_injection(self, text: str) -> bool:
        """
        Check if text contains potential SQL injection patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if potential SQL injection detected
        """
        return bool(self.sql_pattern.search(text.lower()))
    
    def check_xss_attempt(self, text: str) -> bool:
        """
        Check if text contains potential XSS patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if potential XSS detected
        """
        return bool(self.xss_pattern.search(text.lower()))
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file operations.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Keep only alphanumeric, dots, hyphens, and underscores
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Ensure it doesn't start with a dot
        if filename.startswith('.'):
            filename = 'file' + filename
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            name = name[:255-len(ext)-1]
            filename = f"{name}.{ext}" if ext else name
        
        return filename
    
    def sanitize_url(self, url: str) -> Optional[str]:
        """
        Sanitize and validate URL.
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL or None if invalid
        """
        # Basic URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url, re.IGNORECASE):
            return None
        
        # Check for dangerous protocols
        dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                return None
        
        return url.strip()


class RateLimitTracker:
    """Simple rate limiting tracker for API endpoints."""
    
    def __init__(self):
        self._requests: Dict[str, List[datetime]] = {}
        self._blocked_ips: Dict[str, datetime] = {}
    
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 100,
        time_window: int = 3600,  # 1 hour
        block_duration: int = 300  # 5 minutes
    ) -> bool:
        """
        Check if request should be rate limited.
        
        Args:
            identifier: Client identifier (IP, user ID, etc.)
            max_requests: Maximum requests in time window
            time_window: Time window in seconds
            block_duration: Block duration in seconds for violations
            
        Returns:
            True if request should be allowed
        """
        now = datetime.now()
        
        # Check if currently blocked
        if identifier in self._blocked_ips:
            block_time = self._blocked_ips[identifier]
            if (now - block_time).total_seconds() < block_duration:
                return False
            else:
                # Unblock
                del self._blocked_ips[identifier]
        
        # Clean old requests
        cutoff_time = now - timedelta(seconds=time_window)
        if identifier in self._requests:
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier]
                if req_time > cutoff_time
            ]
        else:
            self._requests[identifier] = []
        
        # Check rate limit
        if len(self._requests[identifier]) >= max_requests:
            # Block the identifier
            self._blocked_ips[identifier] = now
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        # Add current request
        self._requests[identifier].append(now)
        return True
    
    def get_remaining_requests(
        self,
        identifier: str,
        max_requests: int = 100,
        time_window: int = 3600
    ) -> int:
        """
        Get remaining requests for identifier.
        
        Args:
            identifier: Client identifier
            max_requests: Maximum requests in time window
            time_window: Time window in seconds
            
        Returns:
            Number of remaining requests
        """
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=time_window)
        
        if identifier not in self._requests:
            return max_requests
        
        # Clean old requests
        recent_requests = [
            req_time for req_time in self._requests[identifier]
            if req_time > cutoff_time
        ]
        
        return max(0, max_requests - len(recent_requests))


class SecurityValidator:
    """Comprehensive security validation for API requests."""
    
    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.rate_limiter = RateLimitTracker()
        self._suspicious_patterns = self._load_suspicious_patterns()
    
    def _load_suspicious_patterns(self) -> List[re.Pattern]:
        """Load patterns for suspicious activity detection."""
        patterns = [
            r'(?i)(union|select|insert|update|delete|drop)\s+',
            r'(?i)<script[^>]*>',
            r'(?i)javascript:',
            r'(?i)\.\./|\.\.\\',
            r'(?i)(cmd|exec|eval|system)\s*\(',
            r'(?i)(wget|curl|powershell)\s+',
        ]
        
        return [re.compile(pattern) for pattern in patterns]
    
    def validate_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize request data.
        
        Args:
            data: Request data dictionary
            
        Returns:
            Validated and sanitized data
        """
        validated_data = {}
        
        for key, value in data.items():
            # Sanitize key
            clean_key = self.sanitizer.sanitize_text(str(key), max_length=100)
            
            # Sanitize value based on type
            if isinstance(value, str):
                clean_value = self._validate_string_value(key, value)
            elif isinstance(value, (int, float)):
                clean_value = self._validate_numeric_value(key, value)
            elif isinstance(value, bool):
                clean_value = value
            elif isinstance(value, list):
                clean_value = [
                    self._validate_string_value(key, str(item))
                    for item in value
                ]
            elif isinstance(value, dict):
                clean_value = self.validate_request_data(value)
            else:
                clean_value = self.sanitizer.sanitize_text(str(value), max_length=1000)
            
            validated_data[clean_key] = clean_value
        
        return validated_data
    
    def _validate_string_value(self, key: str, value: str) -> str:
        """Validate string values based on context."""
        # Special handling for different field types
        if 'email' in key.lower():
            if self.sanitizer.validate_email(value):
                return value.lower().strip()
            else:
                raise ValueError(f"Invalid email format: {value}")
        
        elif 'phone' in key.lower():
            validated_phone = self.sanitizer.validate_phone_number(value)
            if validated_phone:
                return validated_phone
            else:
                raise ValueError(f"Invalid phone number format: {value}")
        
        elif 'url' in key.lower():
            validated_url = self.sanitizer.sanitize_url(value)
            if validated_url:
                return validated_url
            else:
                raise ValueError(f"Invalid URL format: {value}")
        
        else:
            # General text sanitization
            max_length = 10000 if 'content' in key.lower() else 1000
            sanitized = self.sanitizer.sanitize_text(value, max_length=max_length)
            
            # Check for suspicious patterns
            if self._is_suspicious(sanitized):
                logger.warning(f"Suspicious input detected in field {key}: {value[:100]}...")
                raise ValueError("Input contains potentially malicious content")
            
            return sanitized
    
    def _validate_numeric_value(self, key: str, value: Union[int, float]) -> Union[int, float]:
        """Validate numeric values."""
        # Check for reasonable bounds
        if isinstance(value, int):
            if value < -2147483648 or value > 2147483647:  # 32-bit int bounds
                raise ValueError(f"Integer value out of bounds: {value}")
        elif isinstance(value, float):
            if abs(value) > 1e308:  # IEEE 754 double precision bounds
                raise ValueError(f"Float value out of bounds: {value}")
        
        return value
    
    def _is_suspicious(self, text: str) -> bool:
        """Check if text matches suspicious patterns."""
        for pattern in self._suspicious_patterns:
            if pattern.search(text):
                return True
        return False
    
    def generate_csrf_token(self) -> str:
        """Generate a CSRF token."""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, expected_token: str) -> bool:
        """Validate CSRF token."""
        return secrets.compare_digest(token, expected_token)


class PasswordValidator:
    """Password strength validation and hashing utilities."""
    
    def __init__(self):
        self.min_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special = True
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "score": 0,
            "issues": [],
            "suggestions": []
        }
        
        # Length check
        if len(password) < self.min_length:
            results["valid"] = False
            results["issues"].append(f"Password must be at least {self.min_length} characters")
            results["suggestions"].append("Use a longer password")
        else:
            results["score"] += 1
        
        # Character type checks
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            results["valid"] = False
            results["issues"].append("Password must contain uppercase letters")
            results["suggestions"].append("Add uppercase letters (A-Z)")
        else:
            results["score"] += 1
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            results["valid"] = False
            results["issues"].append("Password must contain lowercase letters")
            results["suggestions"].append("Add lowercase letters (a-z)")
        else:
            results["score"] += 1
        
        if self.require_digits and not re.search(r'\d', password):
            results["valid"] = False
            results["issues"].append("Password must contain digits")
            results["suggestions"].append("Add numbers (0-9)")
        else:
            results["score"] += 1
        
        if self.require_special and not any(char in self.special_chars for char in password):
            results["valid"] = False
            results["issues"].append("Password must contain special characters")
            results["suggestions"].append(f"Add special characters ({self.special_chars[:10]}...)")
        else:
            results["score"] += 1
        
        # Additional security checks
        if password.lower() in ["password", "123456", "qwerty", "admin", "letmein"]:
            results["valid"] = False
            results["issues"].append("Password is too common")
            results["suggestions"].append("Use a unique, unpredictable password")
        
        # Strength scoring
        if results["score"] >= 5:
            results["strength"] = "Strong"
        elif results["score"] >= 3:
            results["strength"] = "Moderate"
        else:
            results["strength"] = "Weak"
        
        return results
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using secure algorithm.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        # Add salt and hash
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed_password: Stored hash
            
        Returns:
            True if password matches
        """
        try:
            salt, stored_hash = hashed_password.split(':', 1)
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return secrets.compare_digest(password_hash.hex(), stored_hash)
        except ValueError:
            return False


# Decorator for rate limiting
def rate_limit(max_requests: int = 100, time_window: int = 3600):
    """
    Decorator for rate limiting function calls.
    
    Args:
        max_requests: Maximum requests in time window
        time_window: Time window in seconds
    """
    rate_limiter = RateLimitTracker()
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract identifier (this could be improved based on your needs)
            identifier = kwargs.get('user_id', 'anonymous')
            
            if not rate_limiter.check_rate_limit(identifier, max_requests, time_window):
                raise Exception("Rate limit exceeded")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global instances
input_sanitizer = InputSanitizer()
security_validator = SecurityValidator()
password_validator = PasswordValidator()

__all__ = [
    'InputSanitizer',
    'RateLimitTracker',
    'SecurityValidator', 
    'PasswordValidator',
    'rate_limit',
    'input_sanitizer',
    'security_validator',
    'password_validator'
]