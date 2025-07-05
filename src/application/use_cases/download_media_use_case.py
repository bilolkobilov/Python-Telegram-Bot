import uuid
from typing import List, Optional
from datetime import datetime

from ...domain.entities.download_request import DownloadRequest, DownloadStatus
from ...domain.entities.media import Media
from ...domain.entities.analytics import Analytics
from ...domain.repositories.download_request_repository import DownloadRequestRepository
from ...domain.repositories.user_repository import UserRepository
from ...domain.repositories.analytics_repository import AnalyticsRepository
from ..interfaces.downloader_service import DownloaderService
from ..interfaces.notification_service import NotificationService
from ..interfaces.rate_limiter_service import RateLimiterService
from ..interfaces.translation_service import TranslationService


class DownloadMediaUseCase:
    """Use case for downloading media"""
    
    def __init__(
        self,
        download_request_repository: DownloadRequestRepository,
        user_repository: UserRepository,
        analytics_repository: AnalyticsRepository,
        downloader_service: DownloaderService,
        notification_service: Optional[NotificationService],
        rate_limiter_service: RateLimiterService,
        translation_service: TranslationService
    ):
        self.download_request_repository = download_request_repository
        self.user_repository = user_repository
        self.analytics_repository = analytics_repository
        self.downloader_service = downloader_service
        self.notification_service: Optional[NotificationService] = notification_service
        self.rate_limiter_service = rate_limiter_service
        self.translation_service = translation_service
    
    async def execute(self, user_id: int, url: str, platform: str) -> DownloadRequest:
        """Execute media download"""
        start_time = datetime.now()
        
        # Check if user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Check rate limits
        if await self.rate_limiter_service.is_rate_limited(user_id, "download"):
            reset_time = await self.rate_limiter_service.get_reset_time(user_id, "download")
            message = await self.translation_service.get_translation(
                user.language, "rate_limit_exceeded", reset_time=reset_time
            )
            await self.notification_service.send_error_message(user_id, message)
            raise ValueError("Rate limit exceeded")
        
        # Validate URL
        if not await self.downloader_service.validate_url(url, platform):
            message = await self.translation_service.get_translation(
                user.language, "invalid_url"
            )
            await self.notification_service.send_error_message(user_id, message)
            raise ValueError("Invalid URL")
        
        # Create download request
        request = DownloadRequest(
            id=str(uuid.uuid4()),
            user_id=user_id,
            url=url,
            platform=platform
        )
        
        request = await self.download_request_repository.create(request)
        
        try:
            # Update request status
            request.mark_as_processing()
            await self.download_request_repository.update(request)
            
            # Send progress message
            progress_message = await self.translation_service.get_translation(
                user.language, "download_starting"
            )
            await self.notification_service.send_progress_message(user_id, progress_message)
            
            # Download media
            media_items = await self.downloader_service.download_media(url, platform)
            
            if not media_items:
                raise ValueError("No media found")
            
            # Mark as completed
            request.mark_as_completed(media_items)
            await self.download_request_repository.update(request)
            
            # Send media to user
            for media in media_items:
                # This would be handled by the infrastructure layer
                pass
            
            # Send success message
            await self.notification_service.send_success_message(user_id, len(media_items))
            
            # Update user statistics
            user.increment_downloads()
            await self.user_repository.update(user)
            
            # Increment rate limit usage
            await self.rate_limiter_service.increment_usage(user_id, "download")
            
            # Record analytics
            processing_time = (datetime.now() - start_time).total_seconds()
            analytics = Analytics(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action="download",
                platform=platform,
                success=True,
                processing_time=processing_time
            )
            await self.analytics_repository.create(analytics)
            
        except Exception as e:
            # Mark as failed
            request.mark_as_failed(str(e))
            await self.download_request_repository.update(request)
            
            # Send error message
            error_message = await self.translation_service.get_translation(
                user.language, "download_failed", error=str(e)
            )
            await self.notification_service.send_error_message(user_id, error_message)
            
            # Record analytics
            processing_time = (datetime.now() - start_time).total_seconds()
            analytics = Analytics(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action="download",
                platform=platform,
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
            await self.analytics_repository.create(analytics)
            
            raise
        
        return request