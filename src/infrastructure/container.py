"""
Dependency Injection Container
"""

from typing import Dict, Any
import asyncio

from ..shared.config.settings import Settings
from ..domain.repositories.user_repository import UserRepository
from ..domain.repositories.analytics_repository import AnalyticsRepository
from ..domain.repositories.download_request_repository import DownloadRequestRepository
from ..application.interfaces.downloader_service import DownloaderService
from ..application.interfaces.notification_service import NotificationService
from ..application.interfaces.rate_limiter_service import RateLimiterService
from ..application.interfaces.translation_service import TranslationService
from ..application.use_cases.download_media_use_case import DownloadMediaUseCase
from ..application.use_cases.manage_user_use_case import ManageUserUseCase
from ..application.use_cases.analytics_use_case import AnalyticsUseCase
from ..application.use_cases.admin_use_case import AdminUseCase

# Infrastructure implementations
from .repositories.json_user_repository import JsonUserRepository
from .repositories.json_analytics_repository import JsonAnalyticsRepository
from .repositories.json_download_request_repository import JsonDownloadRequestRepository
from .external_services.instagram_downloader_service import InstagramDownloaderService
from .external_services.tiktok_downloader_service import TikTokDownloaderService
from .external_services.composite_downloader_service import CompositeDownloaderService
from .telegram.telegram_notification_service import TelegramNotificationService
from .external_services.json_rate_limiter_service import JsonRateLimiterService
from .external_services.json_translation_service import JsonTranslationService


class Container:
    """Dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize all services"""
        if self._initialized:
            return
        
        # Initialize repositories
        self._services['user_repository'] = JsonUserRepository(Settings.get_db_file_path("users.json"))
        self._services['analytics_repository'] = JsonAnalyticsRepository(Settings.get_db_file_path("analytics.json"))
        self._services['download_request_repository'] = JsonDownloadRequestRepository(Settings.get_db_file_path("download_requests.json"))
        
        # Initialize external services
        instagram_downloader = InstagramDownloaderService()
        tiktok_downloader = TikTokDownloaderService()
        self._services['downloader_service'] = CompositeDownloaderService([instagram_downloader, tiktok_downloader])
        
        self._services['rate_limiter_service'] = JsonRateLimiterService(Settings.get_db_file_path("rate_limits.json"))
        self._services['translation_service'] = JsonTranslationService("locales")
        
        # Notification service will be initialized when needed with bot instance
        self._services['notification_service'] = None
        
        # Initialize use cases
        self._services['download_media_use_case'] = DownloadMediaUseCase(
            self._services['download_request_repository'],
            self._services['user_repository'],
            self._services['analytics_repository'],
            self._services['downloader_service'],
            self._services['notification_service'],
            self._services['rate_limiter_service'],
            self._services['translation_service']
        )
        
        self._services['manage_user_use_case'] = ManageUserUseCase(
            self._services['user_repository'],
            self._services['notification_service'],
            self._services['translation_service']
        )
        
        self._services['analytics_use_case'] = AnalyticsUseCase(
            self._services['analytics_repository'],
            self._services['user_repository']
        )
        
        self._services['admin_use_case'] = AdminUseCase(
            self._services['user_repository'],
            self._services['analytics_repository'],
            self._services['download_request_repository'],
            self._services['notification_service'],
            self._services['translation_service'],
            self._services['rate_limiter_service']
        )
        
        self._initialized = True
    
    def get_user_repository(self) -> UserRepository:
        """Get user repository"""
        return self._services['user_repository']
    
    def get_analytics_repository(self) -> AnalyticsRepository:
        """Get analytics repository"""
        return self._services['analytics_repository']
    
    def get_download_request_repository(self) -> DownloadRequestRepository:
        """Get download request repository"""
        return self._services['download_request_repository']
    
    def get_downloader_service(self) -> DownloaderService:
        """Get downloader service"""
        return self._services['downloader_service']
    
    def get_notification_service(self) -> NotificationService:
        """Get notification service"""
        return self._services['notification_service']
    
    def get_rate_limiter_service(self) -> RateLimiterService:
        """Get rate limiter service"""
        return self._services['rate_limiter_service']
    
    def get_translation_service(self) -> TranslationService:
        """Get translation service"""
        return self._services['translation_service']
    
    def get_download_media_use_case(self) -> DownloadMediaUseCase:
        """Get download media use case"""
        return self._services['download_media_use_case']
    
    def get_manage_user_use_case(self) -> ManageUserUseCase:
        """Get manage user use case"""
        return self._services['manage_user_use_case']
    
    def get_analytics_use_case(self) -> AnalyticsUseCase:
        """Get analytics use case"""
        return self._services['analytics_use_case']
    
    def get_admin_use_case(self) -> AdminUseCase:
        """Get admin use case"""
        return self._services['admin_use_case']
    
    def set_notification_service(self, service: NotificationService):
        """Set notification service (needed for bot initialization)"""
        self._services['notification_service'] = service
        
        # Update use cases with the new notification service
        self._services['download_media_use_case'].notification_service = service
        self._services['manage_user_use_case'].notification_service = service
        self._services['admin_use_case'].notification_service = service