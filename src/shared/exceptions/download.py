from typing import Optional
from .base import MultisaveXException


class DownloadError(MultisaveXException):
    """Exception raised for download errors"""
    
    def __init__(self, message: str, url: Optional[str] = None, platform: Optional[str] = None):
        super().__init__(message, "DOWNLOAD_ERROR")
        self.url = url
        self.platform = platform    
        if url:
            self.details["url"] = url
        if platform:
            self.details["platform"] = platform


class MediaNotFoundError(DownloadError):
    """Exception raised when media is not found"""
    
    def __init__(self, url: str):
        super().__init__(f"Media not found at URL: {url}", "MEDIA_NOT_FOUND")
        self.url = url
        self.details["url"] = url


class FileSizeExceededError(DownloadError):
    """Exception raised when file size exceeds limit"""
    
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)",
            "FILE_SIZE_EXCEEDED"
        )
        self.file_size = file_size
        self.max_size = max_size
        self.details["file_size"] = file_size
        self.details["max_size"] = max_size


class DownloadTimeoutError(DownloadError):
    """Exception raised when download times out"""
    
    def __init__(self, url: str, timeout: int):
        super().__init__(f"Download timeout ({timeout}s) for URL: {url}", "DOWNLOAD_TIMEOUT")
        self.url = url
        self.timeout = timeout
        self.details["url"] = url
        self.details["timeout"] = timeout