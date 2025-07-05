from typing import Optional, Any
from .base import MultisaveXException


class ValidationError(MultisaveXException):
    """Exception raised for validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value
        if field:
            self.details["field"] = field
        if value is not None:
            self.details["value"] = str(value)


class InvalidURLError(ValidationError):
    """Exception raised for invalid URLs"""
    
    def __init__(self, url: str):
        super().__init__(f"Invalid URL: {url}", "INVALID_URL")
        self.url = url
        self.details["url"] = url


class InvalidPlatformError(ValidationError):
    """Exception raised for invalid platforms"""
    
    def __init__(self, platform: str):
        super().__init__(f"Invalid platform: {platform}", "INVALID_PLATFORM")
        self.platform = platform
        self.details["platform"] = platform