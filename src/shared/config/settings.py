import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings - all sensitive data comes from environment variables"""
    
    # Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_BOT_TOKEN: str = os.getenv("ADMIN_BOT_TOKEN", "")
    ADMIN_IDS: List[int] = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
    
    # Instagram Configuration
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_SESSION_FILE: str = os.getenv("INSTAGRAM_SESSION_FILE", "sessions/instagram.session")
    
    # Environment Detection
    IS_AZURE: bool = bool(os.getenv("WEBSITE_SITE_NAME"))
    IS_PRODUCTION: bool = os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    # File System Configuration
    TEMP_DIR: Path = Path("/tmp" if IS_AZURE else os.getenv("TEMP_DIR", "temp"))
    DB_DIR: Path = Path("/tmp/db" if IS_AZURE else os.getenv("DB_DIR", "db"))
    LOG_FILE: str = "/tmp/multisavex.log" if IS_AZURE else os.getenv("LOG_FILE", "multisavex.log")
    
    # Performance Settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "50"))
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2" if IS_AZURE else "3"))
    CACHE_DURATION: int = int(os.getenv("CACHE_DURATION", "3600"))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    DOWNLOAD_RATE_LIMIT: int = int(os.getenv("DOWNLOAD_RATE_LIMIT", "5"))
    DOWNLOAD_RATE_PERIOD: int = int(os.getenv("DOWNLOAD_RATE_PERIOD", "300"))
    
    # Timeout Settings
    TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "120"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # Feature Flags
    USE_BROWSER_FALLBACK: bool = os.getenv("USE_BROWSER_FALLBACK", "false" if IS_AZURE else "true").lower() == "true"
    ENABLE_CAPTCHA: bool = os.getenv("ENABLE_CAPTCHA", "false").lower() == "true"
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Internationalization
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
    SUPPORTED_LANGUAGES: List[str] = ["en", "ru", "uz"]
    
    # Web Configuration
    WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))
    
    @classmethod
    def validate_required_settings(cls) -> None:
        """Validate that all required settings are present"""
        required_settings = [
            ("BOT_TOKEN", cls.BOT_TOKEN),
            ("ADMIN_BOT_TOKEN", cls.ADMIN_BOT_TOKEN),
        ]
        
        missing_settings = []
        for name, value in required_settings:
            if not value:
                missing_settings.append(name)
        
        if missing_settings:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_settings)}")
    
    @classmethod
    def setup_directories(cls) -> None:
        """Create necessary directories"""
        try:
            cls.TEMP_DIR.mkdir(exist_ok=True, parents=True)
            cls.DB_DIR.mkdir(exist_ok=True, parents=True)
            
            # Create sessions directory
            sessions_dir = Path(cls.INSTAGRAM_SESSION_FILE).parent
            sessions_dir.mkdir(exist_ok=True, parents=True)
            
        except Exception as e:
            import logging
            logging.error(f"Failed to setup directories: {e}")
            raise
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is an admin"""
        return user_id in cls.ADMIN_IDS
    
    @classmethod
    def get_temp_file_path(cls, filename: str) -> Path:
        """Get temporary file path"""
        return cls.TEMP_DIR / filename
    
    @classmethod
    def get_db_file_path(cls, filename: str) -> Path:
        """Get database file path"""
        return cls.DB_DIR / filename