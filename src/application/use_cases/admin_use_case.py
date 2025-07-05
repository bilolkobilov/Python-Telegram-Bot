from typing import List, Dict, Optional
from datetime import datetime

from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository
from ...domain.repositories.analytics_repository import AnalyticsRepository
from ...domain.repositories.download_request_repository import DownloadRequestRepository
from ..interfaces.notification_service import NotificationService
from ..interfaces.translation_service import TranslationService
from ..interfaces.rate_limiter_service import RateLimiterService


class AdminUseCase:
    """Use case for admin operations"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        analytics_repository: AnalyticsRepository,
        download_request_repository: DownloadRequestRepository,
        notification_service: Optional[NotificationService],
        translation_service: TranslationService,
        rate_limiter_service: RateLimiterService
    ):
        self.user_repository = user_repository
        self.analytics_repository = analytics_repository
        self.download_request_repository = download_request_repository
        self.notification_service: Optional[NotificationService] = notification_service
        self.translation_service = translation_service
        self.rate_limiter_service = rate_limiter_service
    
    async def get_system_stats(self) -> Dict:
        """Get system statistics"""
        all_users = await self.user_repository.get_all()
        active_users = await self.user_repository.get_active_users(days=30)
        banned_users = await self.user_repository.get_banned_users()
        
        total_downloads = await self.analytics_repository.get_total_downloads()
        platform_stats = await self.analytics_repository.get_platform_stats()
        
        pending_requests = await self.download_request_repository.get_pending_requests()
        processing_requests = await self.download_request_repository.get_processing_requests()
        
        return {
            "users": {
                "total": len(all_users),
                "active": len(active_users),
                "banned": len(banned_users)
            },
            "downloads": {
                "total": total_downloads,
                "platform_breakdown": platform_stats
            },
            "requests": {
                "pending": len(pending_requests),
                "processing": len(processing_requests)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_user_list(self, page: int = 1, limit: int = 50) -> Dict:
        """Get paginated user list"""
        all_users = await self.user_repository.get_all()
        
        # Simple pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_users = all_users[start_idx:end_idx]
        
        user_data = []
        for user in paginated_users:
            user_data.append({
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language": user.language,
                "download_count": user.download_count,
                "is_banned": user.is_banned,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_active": user.last_active.isoformat() if user.last_active else None
            })
        
        return {
            "users": user_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(all_users),
                "pages": (len(all_users) + limit - 1) // limit
            }
        }
    
    async def broadcast_message(self, message: str, target_language: Optional[str] = None) -> Dict:
        """Broadcast message to users"""
        if target_language:
            users = await self.user_repository.get_users_by_language(target_language)
        else:
            users = await self.user_repository.get_all()
        
        # Filter out banned users
        active_users = [user for user in users if not user.is_banned]
        
        sent_count = await self.notification_service.broadcast_message(active_users, message)
        
        return {
            "message": message,
            "target_language": target_language,
            "total_users": len(active_users),
            "sent_count": sent_count
        }
    
    async def manage_user_ban(self, user_id: int, banned: bool, admin_id: int) -> User:
        """Ban or unban a user"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if banned:
            user.ban_user()
            message_key = "user_banned"
        else:
            user.unban_user()
            message_key = "user_unbanned"
        
        user = await self.user_repository.update(user)
        
        # Send notification to user
        notification_message = await self.translation_service.get_translation(
            user.language, message_key
        )
        await self.notification_service.send_message(user_id, notification_message)
        
        return user
    
    async def reset_user_limits(self, user_id: int) -> bool:
        """Reset user rate limits"""
        return await self.rate_limiter_service.reset_user_limits(user_id)
    
    async def cleanup_system(self) -> Dict:
        """Clean up old data"""
        analytics_cleaned = await self.analytics_repository.cleanup_old_records(days=90)
        requests_cleaned = await self.download_request_repository.cleanup_old_requests(days=30)
        limits_cleaned = await self.rate_limiter_service.cleanup_expired_limits()
        
        return {
            "analytics_records_cleaned": analytics_cleaned,
            "requests_cleaned": requests_cleaned,
            "rate_limits_cleaned": limits_cleaned,
            "timestamp": datetime.now().isoformat()
        }