from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class RateLimiterService(ABC):
    """Abstract rate limiter service interface"""
    
    @abstractmethod
    async def is_rate_limited(self, user_id: int, action: str = "download") -> bool:
        """Check if user is rate limited for specific action"""
        pass
    
    @abstractmethod
    async def get_rate_limit_info(self, user_id: int, action: str = "download") -> Dict[str, Any]:
        """
        Get rate limit information for user
        
        Returns:
            Dict containing:
            - remaining: number of remaining requests
            - reset_time: when the limit resets
            - total_limit: total requests allowed in period
            - used: requests used in current period
        """
        pass
    
    @abstractmethod
    async def increment_usage(self, user_id: int, action: str = "download") -> bool:
        """Increment usage count for user and action"""
        pass
    
    @abstractmethod
    async def reset_user_limits(self, user_id: int) -> bool:
        """Reset all rate limits for a user (admin function)"""
        pass
    
    @abstractmethod
    async def set_custom_limit(
        self, 
        user_id: int, 
        action: str, 
        limit: int, 
        period_seconds: int
    ) -> bool:
        """Set custom rate limit for specific user"""
        pass
    
    @abstractmethod
    async def get_time_until_reset(self, user_id: int, action: str = "download") -> Optional[timedelta]:
        """Get time until rate limit resets"""
        pass
    
    @abstractmethod
    async def is_user_blocked(self, user_id: int) -> bool:
        """Check if user is completely blocked"""
        pass
    
    @abstractmethod
    async def block_user(self, user_id: int, duration_hours: Optional[int] = None) -> bool:
        """Block user for specified duration (None = permanent)"""
        pass
    
    @abstractmethod
    async def unblock_user(self, user_id: int) -> bool:
        """Unblock user"""
        pass
    
    @abstractmethod
    async def cleanup_expired_limits(self) -> int:
        """Clean up expired rate limit entries"""
        pass