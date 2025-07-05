import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ...application.interfaces.rate_limiter_service import RateLimiterService
from ...shared.exceptions import RepositoryError
from ...shared.config.settings import Settings

logger = logging.getLogger(__name__)


class JsonRateLimiterService(RateLimiterService):
    """JSON-based rate limiter service implementation"""
    
    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._lock = asyncio.Lock()
        self._ensure_file_exists()
        
        # Default rate limits
        self.default_limits = {
            "download": {
                "requests": Settings.DOWNLOAD_RATE_LIMIT,
                "period_seconds": Settings.DOWNLOAD_RATE_PERIOD
            },
            "message": {
                "requests": Settings.RATE_LIMIT_REQUESTS,
                "period_seconds": Settings.RATE_LIMIT_PERIOD
            }
        }
    
    def _ensure_file_exists(self):
        """Ensure the JSON file exists"""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                self.file_path.write_text("{}", encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to ensure rate limiter file exists: {e}")
            raise RepositoryError(f"Failed to initialize rate limiter: {e}")
    
    async def _read_data(self) -> Dict[str, Any]:
        """Read data from JSON file"""
        try:
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None, 
                lambda: self.file_path.read_text(encoding="utf-8")
            )
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in rate limiter file: {e}")
            # Reset file if corrupted
            await self._write_data({})
            return {}
        except Exception as e:
            logger.error(f"Error reading rate limiter data: {e}")
            raise RepositoryError(f"Failed to read rate limiter data: {e}")
    
    async def _write_data(self, data: Dict[str, Any]):
        """Write data to JSON file"""
        try:
            loop = asyncio.get_event_loop()
            content = json.dumps(data, indent=2, default=str, ensure_ascii=False)
            await loop.run_in_executor(
                None,
                lambda: self.file_path.write_text(content, encoding="utf-8")
            )
        except Exception as e:
            logger.error(f"Error writing rate limiter data: {e}")
            raise RepositoryError(f"Failed to write rate limiter data: {e}")
    
    def _get_user_key(self, user_id: int) -> str:
        """Get user key for storage"""
        return f"user_{user_id}"
    
    def _get_action_key(self, action: str) -> str:
        """Get action key for storage"""
        return f"action_{action}"
    
    async def is_rate_limited(self, user_id: int, action: str = "download") -> bool:
        """Check if user is rate limited for specific action"""
        try:
            # Check if user is blocked
            if await self.is_user_blocked(user_id):
                return True
            
            data = await self._read_data()
            user_key = self._get_user_key(user_id)
            action_key = self._get_action_key(action)
            
            # Get user data
            user_data = data.get(user_key, {})
            action_data = user_data.get(action_key, {})
            
            if not action_data:
                return False
            
            # Get limit configuration
            custom_limits = user_data.get("custom_limits", {})
            if action in custom_limits:
                limit_config = custom_limits[action]
            else:
                limit_config = self.default_limits.get(action, {
                    "requests": 10,
                    "period_seconds": 60
                })
            
            # Check if within time window
            reset_time = datetime.fromisoformat(action_data.get("reset_time", "2000-01-01T00:00:00"))
            current_time = datetime.now()
            
            if current_time >= reset_time:
                # Reset the counter
                return False
            
            # Check if limit exceeded
            used_requests = action_data.get("used", 0)
            max_requests = limit_config["requests"]
            
            return used_requests >= max_requests
            
        except Exception as e:
            logger.error(f"Error checking rate limit for user {user_id}: {e}")
            return False  # Fail open to avoid blocking users on errors
    
    async def get_rate_limit_info(self, user_id: int, action: str = "download") -> Dict[str, Any]:
        """Get rate limit information for user"""
        try:
            data = await self._read_data()
            user_key = self._get_user_key(user_id)
            action_key = self._get_action_key(action)
            
            user_data = data.get(user_key, {})
            action_data = user_data.get(action_key, {})
            
            # Get limit configuration
            custom_limits = user_data.get("custom_limits", {})
            if action in custom_limits:
                limit_config = custom_limits[action]
            else:
                limit_config = self.default_limits.get(action, {
                    "requests": 10,
                    "period_seconds": 60
                })
            
            current_time = datetime.now()
            reset_time = datetime.fromisoformat(action_data.get("reset_time", current_time.isoformat()))
            used_requests = action_data.get("used", 0)
            total_limit = limit_config["requests"]
            
            # If past reset time, reset counters
            if current_time >= reset_time:
                used_requests = 0
                reset_time = current_time + timedelta(seconds=limit_config["period_seconds"])
            
            remaining = max(0, total_limit - used_requests)
            
            return {
                "remaining": remaining,
                "reset_time": reset_time.isoformat(),
                "total_limit": total_limit,
                "used": used_requests,
                "period_seconds": limit_config["period_seconds"]
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit info for user {user_id}: {e}")
            return {
                "remaining": 0,
                "reset_time": datetime.now().isoformat(),
                "total_limit": 0,
                "used": 0,
                "period_seconds": 60
            }
    
    async def increment_usage(self, user_id: int, action: str = "download") -> bool:
        """Increment usage count for user and action"""
        async with self._lock:
            try:
                data = await self._read_data()
                user_key = self._get_user_key(user_id)
                action_key = self._get_action_key(action)
                
                # Initialize user data if needed
                if user_key not in data:
                    data[user_key] = {}
                
                user_data = data[user_key]
                
                # Get limit configuration
                custom_limits = user_data.get("custom_limits", {})
                if action in custom_limits:
                    limit_config = custom_limits[action]
                else:
                    limit_config = self.default_limits.get(action, {
                        "requests": 10,
                        "period_seconds": 60
                    })
                
                current_time = datetime.now()
                
                # Initialize or reset action data if needed
                if action_key not in user_data:
                    user_data[action_key] = {
                        "used": 0,
                        "reset_time": (current_time + timedelta(seconds=limit_config["period_seconds"])).isoformat()
                    }
                
                action_data = user_data[action_key]
                reset_time = datetime.fromisoformat(action_data["reset_time"])
                
                # Reset if past reset time
                if current_time >= reset_time:
                    action_data["used"] = 0
                    action_data["reset_time"] = (current_time + timedelta(seconds=limit_config["period_seconds"])).isoformat()
                
                # Increment usage
                action_data["used"] += 1
                
                await self._write_data(data)
                logger.debug(f"Incremented {action} usage for user {user_id}: {action_data['used']}")
                return True
                
            except Exception as e:
                logger.error(f"Error incrementing usage for user {user_id}: {e}")
                return False
    
    async def reset_user_limits(self, user_id: int) -> bool:
        """Reset all rate limits for a user (admin function)"""
        async with self._lock:
            try:
                data = await self._read_data()
                user_key = self._get_user_key(user_id)
                
                if user_key in data:
                    # Keep custom limits and blocked status, but reset counters
                    user_data = data[user_key]
                    custom_limits = user_data.get("custom_limits", {})
                    blocked_until = user_data.get("blocked_until")
                    
                    data[user_key] = {
                        "custom_limits": custom_limits
                    }
                    
                    if blocked_until:
                        data[user_key]["blocked_until"] = blocked_until
                    
                    await self._write_data(data)
                    logger.info(f"Reset rate limits for user {user_id}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error resetting limits for user {user_id}: {e}")
                return False
    
    async def set_custom_limit(
        self, 
        user_id: int, 
        action: str, 
        limit: int, 
        period_seconds: int
    ) -> bool:
        """Set custom rate limit for specific user"""
        async with self._lock:
            try:
                data = await self._read_data()
                user_key = self._get_user_key(user_id)
                
                if user_key not in data:
                    data[user_key] = {}
                
                if "custom_limits" not in data[user_key]:
                    data[user_key]["custom_limits"] = {}
                
                data[user_key]["custom_limits"][action] = {
                    "requests": limit,
                    "period_seconds": period_seconds
                }
                
                await self._write_data(data)
                logger.info(f"Set custom limit for user {user_id}, action {action}: {limit}/{period_seconds}s")
                return True
                
            except Exception as e:
                logger.error(f"Error setting custom limit for user {user_id}: {e}")
                return False
    
    async def get_time_until_reset(self, user_id: int, action: str = "download") -> Optional[timedelta]:
        """Get time until rate limit resets"""
        try:
            rate_info = await self.get_rate_limit_info(user_id, action)
            reset_time = datetime.fromisoformat(rate_info["reset_time"])
            current_time = datetime.now()
            
            if reset_time > current_time:
                return reset_time - current_time
            else:
                return timedelta(0)
                
        except Exception as e:
            logger.error(f"Error getting reset time for user {user_id}: {e}")
            return None
    
    async def is_user_blocked(self, user_id: int) -> bool:
        """Check if user is completely blocked"""
        try:
            data = await self._read_data()
            user_key = self._get_user_key(user_id)
            user_data = data.get(user_key, {})
            
            blocked_until = user_data.get("blocked_until")
            if not blocked_until:
                return False
            
            if blocked_until == "permanent":
                return True
            
            # Check if temporary block has expired
            block_time = datetime.fromisoformat(blocked_until)
            return datetime.now() < block_time
            
        except Exception as e:
            logger.error(f"Error checking if user {user_id} is blocked: {e}")
            return False
    
    async def block_user(self, user_id: int, duration_hours: Optional[int] = None) -> bool:
        """Block user for specified duration (None = permanent)"""
        async with self._lock:
            try:
                data = await self._read_data()
                user_key = self._get_user_key(user_id)
                
                if user_key not in data:
                    data[user_key] = {}
                
                if duration_hours is None:
                    data[user_key]["blocked_until"] = "permanent"
                else:
                    block_until = datetime.now() + timedelta(hours=duration_hours)
                    data[user_key]["blocked_until"] = block_until.isoformat()
                
                await self._write_data(data)
                logger.info(f"Blocked user {user_id} for {duration_hours or 'permanent'} hours")
                return True
                
            except Exception as e:
                logger.error(f"Error blocking user {user_id}: {e}")
                return False
    
    async def unblock_user(self, user_id: int) -> bool:
        """Unblock user"""
        async with self._lock:
            try:
                data = await self._read_data()
                user_key = self._get_user_key(user_id)
                
                if user_key in data and "blocked_until" in data[user_key]:
                    del data[user_key]["blocked_until"]
                    await self._write_data(data)
                    logger.info(f"Unblocked user {user_id}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error unblocking user {user_id}: {e}")
                return False
    
    async def cleanup_expired_limits(self) -> int:
        """Clean up expired rate limit entries"""
        async with self._lock:
            try:
                data = await self._read_data()
                current_time = datetime.now()
                cleaned_count = 0
                
                for user_key, user_data in list(data.items()):
                    # Clean up expired action data
                    for action_key, action_data in list(user_data.items()):
                        if action_key.startswith("action_") and isinstance(action_data, dict):
                            reset_time = datetime.fromisoformat(action_data.get("reset_time", current_time.isoformat()))
                            if current_time >= reset_time:
                                del user_data[action_key]
                                cleaned_count += 1
                    
                    # Clean up expired blocks
                    blocked_until = user_data.get("blocked_until")
                    if blocked_until and blocked_until != "permanent":
                        try:
                            block_time = datetime.fromisoformat(blocked_until)
                            if current_time >= block_time:
                                del user_data["blocked_until"]
                                cleaned_count += 1
                        except ValueError:
                            pass
                    
                    # Remove empty user entries
                    if not user_data or (len(user_data) == 1 and "custom_limits" in user_data and not user_data["custom_limits"]):
                        del data[user_key]
                        cleaned_count += 1
                
                if cleaned_count > 0:
                    await self._write_data(data)
                    logger.info(f"Cleaned up {cleaned_count} expired rate limit entries")
                
                return cleaned_count
                
            except Exception as e:
                logger.error(f"Error cleaning up expired limits: {e}")
                return 0 