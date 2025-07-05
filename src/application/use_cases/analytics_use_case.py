from typing import Dict, List
from datetime import datetime, timedelta

from ...domain.entities.analytics import Analytics
from ...domain.repositories.analytics_repository import AnalyticsRepository
from ...domain.repositories.user_repository import UserRepository


class AnalyticsUseCase:
    """Use case for analytics management"""
    
    def __init__(
        self,
        analytics_repository: AnalyticsRepository,
        user_repository: UserRepository
    ):
        self.analytics_repository = analytics_repository
        self.user_repository = user_repository
    
    async def get_overview_stats(self) -> Dict:
        """Get overview statistics"""
        total_downloads = await self.analytics_repository.get_total_downloads()
        platform_stats = await self.analytics_repository.get_platform_stats()
        error_stats = await self.analytics_repository.get_error_stats()
        avg_processing_time = await self.analytics_repository.get_average_processing_time()
        
        # Get user statistics
        all_users = await self.user_repository.get_all()
        active_users = await self.user_repository.get_active_users(days=30)
        
        return {
            "total_downloads": total_downloads,
            "total_users": len(all_users),
            "active_users": len(active_users),
            "platform_stats": platform_stats,
            "error_stats": error_stats,
            "avg_processing_time": avg_processing_time
        }
    
    async def get_daily_stats(self, days: int = 30) -> Dict[str, int]:
        """Get daily statistics"""
        return await self.analytics_repository.get_daily_stats(days)
    
    async def get_top_users(self, limit: int = 10) -> List[Dict]:
        """Get top users by downloads"""
        users = await self.user_repository.get_top_users(limit)
        return [
            {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "download_count": user.download_count,
                "last_active": user.last_active.isoformat() if user.last_active else None
            }
            for user in users
        ]
    
    async def get_platform_breakdown(self) -> Dict[str, int]:
        """Get platform usage breakdown"""
        return await self.analytics_repository.get_platform_stats()
    
    async def get_error_analysis(self) -> Dict:
        """Get error analysis"""
        error_stats = await self.analytics_repository.get_error_stats()
        total_downloads = await self.analytics_repository.get_total_downloads()
        
        success_rate = 0
        if total_downloads > 0:
            failed_downloads = sum(error_stats.values())
            success_rate = ((total_downloads - failed_downloads) / total_downloads) * 100
        
        return {
            "error_breakdown": error_stats,
            "success_rate": success_rate,
            "total_errors": sum(error_stats.values())
        }
    
    async def get_user_activity_stats(self, days: int = 30) -> Dict:
        """Get user activity statistics"""
        active_users = await self.user_repository.get_active_users(days)
        all_users = await self.user_repository.get_all()
        
        # Group by language
        language_stats = {}
        for user in all_users:
            language = user.language
            if language not in language_stats:
                language_stats[language] = 0
            language_stats[language] += 1
        
        return {
            "active_users": len(active_users),
            "total_users": len(all_users),
            "activity_rate": (len(active_users) / len(all_users)) * 100 if all_users else 0,
            "language_breakdown": language_stats
        }
    
    async def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Clean up old data"""
        analytics_cleaned = await self.analytics_repository.cleanup_old_records(days)
        
        return {
            "analytics_records_cleaned": analytics_cleaned
        }