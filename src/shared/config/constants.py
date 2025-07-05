from enum import Enum


class Constants:
    """Application constants"""
    
    # File Extensions
    VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    
    # Platform Names
    PLATFORM_INSTAGRAM = "instagram"
    PLATFORM_TIKTOK = "tiktok"
    SUPPORTED_PLATFORMS = [PLATFORM_INSTAGRAM, PLATFORM_TIKTOK]
    
    # Rate Limiting Actions
    ACTION_DOWNLOAD = "download"
    ACTION_MESSAGE = "message"
    ACTION_COMMAND = "command"
    
    # Database File Names
    DB_USERS = "users.json"
    DB_ANALYTICS = "analytics.json"
    DB_RATE_LIMITS = "rate_limits.json"
    DB_FILE_CACHE = "file_cache.json"
    
    # Message Types
    MESSAGE_TYPE_TEXT = "text"
    MESSAGE_TYPE_PHOTO = "photo"
    MESSAGE_TYPE_VIDEO = "video"
    MESSAGE_TYPE_DOCUMENT = "document"
    
    # Bot Commands
    COMMAND_START = "start"
    COMMAND_HELP = "help"
    COMMAND_LANGUAGE = "language"
    COMMAND_STATS = "stats"
    
    # Callback Data Prefixes
    CALLBACK_LANG = "lang_"
    CALLBACK_ADMIN = "admin_"
    CALLBACK_STATS = "stats_"
    
    # Error Messages
    ERROR_INVALID_URL = "Invalid URL provided"
    ERROR_UNSUPPORTED_PLATFORM = "Unsupported platform"
    ERROR_RATE_LIMIT_EXCEEDED = "Rate limit exceeded"
    ERROR_DOWNLOAD_FAILED = "Download failed"
    ERROR_USER_BANNED = "User is banned"
    ERROR_INTERNAL_ERROR = "Internal server error"
    
    # Success Messages
    SUCCESS_DOWNLOAD_COMPLETE = "Download completed successfully"
    SUCCESS_LANGUAGE_CHANGED = "Language changed successfully"
    SUCCESS_USER_REGISTERED = "User registered successfully"
    
    # Default Values
    DEFAULT_LANGUAGE = "en"
    DEFAULT_PAGE_SIZE = 50
    DEFAULT_TIMEOUT = 120
    DEFAULT_MAX_RETRIES = 3
    
    # File Size Limits (in bytes)
    MAX_TELEGRAM_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_INSTAGRAM_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    # Cache Keys
    CACHE_KEY_USER = "user_{user_id}"
    CACHE_KEY_ANALYTICS = "analytics_{date}"
    CACHE_KEY_RATE_LIMIT = "rate_limit_{user_id}_{action}"


class Platform(Enum):
    """Platform enumeration"""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class Language(Enum):
    """Language enumeration"""
    ENGLISH = "en"
    RUSSIAN = "ru"
    UZBEK = "uz"


class UserRole(Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"