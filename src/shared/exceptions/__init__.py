"""
Custom exceptions for MultisaveX application
"""


class MultisaveXException(Exception):
    """Base exception for MultisaveX application"""
    pass


class ConfigurationError(MultisaveXException):
    """Raised when there's a configuration error"""
    pass


class RepositoryError(MultisaveXException):
    """Raised when there's a repository operation error"""
    pass


class DownloadError(MultisaveXException):
    """Raised when media download fails"""
    pass


class UnsupportedUrlError(DownloadError):
    """Raised when URL is not supported"""
    pass


class RateLimitError(MultisaveXException):
    """Raised when rate limit is exceeded"""
    pass


class ValidationError(MultisaveXException):
    """Raised when validation fails"""
    pass


class NotificationError(MultisaveXException):
    """Raised when notification sending fails"""
    pass


class TranslationError(MultisaveXException):
    """Raised when translation fails"""
    pass


class ServiceUnavailableError(MultisaveXException):
    """Raised when external service is unavailable"""
    pass


class AuthenticationError(MultisaveXException):
    """Raised when authentication fails"""
    pass


class UserBannedError(MultisaveXException):
    """Raised when user is banned"""
    pass


class FileSizeError(DownloadError):
    """Raised when file size exceeds limits"""
    pass


class TimeoutError(MultisaveXException):
    """Raised when operation times out"""
    pass

__all__ = [
    'MultisaveXException',
    'ValidationError',
    'RateLimitError',
    'DownloadError',
    'UnsupportedUrlError',
    'ConfigurationError',
    'RepositoryError',
    'NotificationError',
    'TranslationError',
    'ServiceUnavailableError',
    'AuthenticationError',
    'UserBannedError',
    'FileSizeError',
    'TimeoutError'
]