import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from ...domain.entities.analytics import Analytics, AnalyticsEventType
from ...domain.repositories.analytics_repository import AnalyticsRepository
from ...shared.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class JsonAnalyticsRepository(AnalyticsRepository):
    """JSON-based analytics repository implementation"""
    
    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._lock = asyncio.Lock()
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure the JSON file exists"""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                self.file_path.write_text("[]", encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to ensure analytics file exists: {e}")
            raise RepositoryError(f"Failed to initialize analytics repository: {e}")
    
    async def _read_data(self) -> List[Dict[str, Any]]:
        """Read data from JSON file"""
        try:
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None, 
                lambda: self.file_path.read_text(encoding="utf-8")
            )
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in analytics repository: {e}")
            # Reset file if corrupted
            await self._write_data([])
            return []
        except Exception as e:
            logger.error(f"Error reading analytics data: {e}")
            raise RepositoryError(f"Failed to read analytics data: {e}")
    
    async def _write_data(self, data: List[Dict[str, Any]]):
        """Write data to JSON file"""
        try:
            loop = asyncio.get_event_loop()
            content = json.dumps(data, indent=2, default=str, ensure_ascii=False)
            await loop.run_in_executor(
                None,
                lambda: self.file_path.write_text(content, encoding="utf-8")
            )
        except Exception as e:
            logger.error(f"Error writing analytics data: {e}")
            raise RepositoryError(f"Failed to write analytics data: {e}")
    
    def _analytics_to_dict(self, analytics: Analytics) -> Dict[str, Any]:
        """Convert Analytics entity to dictionary"""
        return {
            "id": analytics.id,
            "user_id": analytics.user_id,
            "event_type": analytics.event_type.value,
            "platform": analytics.platform,
            "media_type": analytics.media_type,
            "url": analytics.url,
            "file_size": analytics.file_size,
            "processing_time": analytics.processing_time,
            "success": analytics.success,
            "error_message": analytics.error_message,
            "metadata": analytics.metadata,
            "created_at": analytics.created_at.isoformat() if analytics.created_at else None
        }
    
    def _dict_to_analytics(self, data: Dict[str, Any]) -> Analytics:
        """Convert dictionary to Analytics entity"""
        return Analytics(
            id=data["id"],
            user_id=data["user_id"],
            event_type=AnalyticsEventType(data["event_type"]),
            platform=data.get("platform"),
            media_type=data.get("media_type"),
            url=data.get("url"),
            file_size=data.get("file_size"),
            processing_time=data.get("processing_time"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )
    
    async def save(self, analytics: Analytics) -> Analytics:
        """Save analytics record"""
        async with self._lock:
            try:
                data = await self._read_data()
                analytics_dict = self._analytics_to_dict(analytics)
                data.append(analytics_dict)
                await self._write_data(data)
                logger.debug(f"Saved analytics record {analytics.id}")
                return analytics
            except Exception as e:
                logger.error(f"Error saving analytics {analytics.id}: {e}")
                raise RepositoryError(f"Failed to save analytics: {e}")
    
    async def get_by_user_id(self, user_id: int, days: int = 30) -> List[Analytics]:
        """Get analytics for a specific user"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            data = await self._read_data()
            user_analytics = []
            
            for record in data:
                if record["user_id"] == user_id:
                    created_at = datetime.fromisoformat(record["created_at"]) if record.get("created_at") else datetime.now()
                    if created_at >= cutoff_date:
                        user_analytics.append(self._dict_to_analytics(record))
            
            return user_analytics
        except Exception as e:
            logger.error(f"Error getting analytics for user {user_id}: {e}")
            raise RepositoryError(f"Failed to get user analytics: {e}")
    
    async def get_platform_stats(self, platform: str, days: int = 30) -> Dict[str, Any]:
        """Get platform-specific statistics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            data = await self._read_data()
            
            stats = {
                "total_downloads": 0,
                "successful_downloads": 0,
                "failed_downloads": 0,
                "unique_users": set(),
                "media_types": defaultdict(int),
                "average_processing_time": 0,
                "total_file_size": 0
            }
            
            processing_times = []
            
            for record in data:
                if record.get("platform") == platform:
                    created_at = datetime.fromisoformat(record["created_at"]) if record.get("created_at") else datetime.now()
                    if created_at >= cutoff_date:
                        event_type = record.get("event_type")
                        
                        if event_type in ["download_success", "download_failed"]:
                            stats["total_downloads"] += 1
                            stats["unique_users"].add(record["user_id"])
                            
                            if event_type == "download_success":
                                stats["successful_downloads"] += 1
                                if record.get("file_size"):
                                    stats["total_file_size"] += record["file_size"]
                            else:
                                stats["failed_downloads"] += 1
                            
                            if record.get("media_type"):
                                stats["media_types"][record["media_type"]] += 1
                            
                            if record.get("processing_time"):
                                processing_times.append(record["processing_time"])
            
            stats["unique_users"] = len(stats["unique_users"])
            stats["media_types"] = dict(stats["media_types"])
            stats["average_processing_time"] = sum(processing_times) / len(processing_times) if processing_times else 0
            stats["success_rate"] = (stats["successful_downloads"] / stats["total_downloads"]) * 100 if stats["total_downloads"] > 0 else 0
            
            return stats
        except Exception as e:
            logger.error(f"Error getting platform stats for {platform}: {e}")
            raise RepositoryError(f"Failed to get platform stats: {e}")
    
    async def get_daily_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get daily usage statistics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            data = await self._read_data()
            
            daily_stats: Dict[str, Dict[str, Any]] = {}
            
            for record in data:
                created_at = datetime.fromisoformat(record["created_at"]) if record.get("created_at") else datetime.now()
                if created_at >= cutoff_date:
                    date_key = created_at.strftime("%Y-%m-%d")
                    event_type = record.get("event_type")
                    
                    if event_type in ["download_success", "download_failed"]:
                        # Initialize date entry if it doesn't exist
                        if date_key not in daily_stats:
                            daily_stats[date_key] = {
                                "downloads": 0,
                                "successful": 0,
                                "failed": 0,
                                "unique_users": set(),
                                "platforms": {}
                            }
                        
                        daily_stats[date_key]["downloads"] += 1
                        daily_stats[date_key]["unique_users"].add(record["user_id"])
                        
                        if event_type == "download_success":
                            daily_stats[date_key]["successful"] += 1
                        else:
                            daily_stats[date_key]["failed"] += 1
                        
                        platform = record.get("platform")
                        if platform:
                            platforms = daily_stats[date_key]["platforms"]
                            platforms[platform] = platforms.get(platform, 0) + 1
            
            # Convert sets to counts for final result
            result = {}
            for date, stats in daily_stats.items():
                result[date] = {
                    "downloads": stats["downloads"],
                    "successful": stats["successful"],
                    "failed": stats["failed"],
                    "unique_users": len(stats["unique_users"]),
                    "platforms": stats["platforms"]
                }
            
            return result
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            raise RepositoryError(f"Failed to get daily stats: {e}")
    
    async def get_total_downloads(self) -> int:
        """Get total download count"""
        try:
            data = await self._read_data()
            return sum(1 for record in data if record.get("event_type") in ["download_success", "download_failed"])
        except Exception as e:
            logger.error(f"Error getting total downloads: {e}")
            raise RepositoryError(f"Failed to get total downloads: {e}")
    
    async def get_downloads_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Analytics]:
        """Get downloads within date range"""
        try:
            data = await self._read_data()
            downloads = []
            
            for record in data:
                created_at = datetime.fromisoformat(record["created_at"]) if record.get("created_at") else datetime.now()
                if start_date <= created_at <= end_date:
                    event_type = record.get("event_type")
                    if event_type in ["download_success", "download_failed"]:
                        downloads.append(self._dict_to_analytics(record))
            
            return downloads
        except Exception as e:
            logger.error(f"Error getting downloads by date range: {e}")
            raise RepositoryError(f"Failed to get downloads by date range: {e}")
    
    async def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by download count"""
        try:
            data = await self._read_data()
            user_downloads = defaultdict(int)
            
            for record in data:
                event_type = record.get("event_type")
                if event_type == "download_success":
                    user_downloads[record["user_id"]] += 1
            
            # Sort by download count and take top users
            top_users = sorted(user_downloads.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            return [{"user_id": user_id, "download_count": count} for user_id, count in top_users]
        except Exception as e:
            logger.error(f"Error getting top users: {e}")
            raise RepositoryError(f"Failed to get top users: {e}") 