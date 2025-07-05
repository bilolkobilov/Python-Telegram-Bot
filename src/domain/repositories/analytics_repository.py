from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..entities.analytics import Analytics


class AnalyticsRepository(ABC):
    """Abstract analytics repository interface"""
    
    @abstractmethod
    async def save(self, analytics: Analytics) -> Analytics:
        """Save analytics record"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int, days: int = 30) -> List[Analytics]:
        """Get analytics for a specific user"""
        pass
    
    @abstractmethod
    async def get_platform_stats(self, platform: str, days: int = 30) -> Dict[str, Any]:
        """Get platform-specific statistics"""
        pass
    
    @abstractmethod
    async def get_daily_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get daily usage statistics"""
        pass
    
    @abstractmethod
    async def get_total_downloads(self) -> int:
        """Get total download count"""
        pass
    
    @abstractmethod
    async def get_downloads_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Analytics]:
        """Get downloads within date range"""
        pass
    
    @abstractmethod
    async def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by download count"""
        pass