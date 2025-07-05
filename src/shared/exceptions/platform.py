from typing import Optional
from .base import MultisaveXException


class UnsupportedPlatformError(MultisaveXException):
    """Exception raised for unsupported platforms"""
    
    def __init__(self, platform: str):
        super().__init__(f"Unsupported platform: {platform}", "UNSUPPORTED_PLATFORM")
        self.platform = platform
        self.details["platform"] = platform


class PlatformAPIError(MultisaveXException):
    """Exception raised for platform API errors"""
    
    def __init__(self, platform: str, message: str, status_code: Optional[int] = None):
        super().__init__(f"Platform API error ({platform}): {message}", "PLATFORM_API_ERROR")
        self.platform = platform
        self.status_code = status_code
        self.details["platform"] = platform
        if status_code:
            self.details["status_code"] = status_code


class PlatformAuthenticationError(MultisaveXException):
    """Exception raised for platform authentication errors"""
    
    def __init__(self, platform: str):
        super().__init__(f"Authentication failed for platform: {platform}", "PLATFORM_AUTH_ERROR")
        self.platform = platform
        self.details["platform"] = platform