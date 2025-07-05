import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ...domain.entities.download_request import DownloadRequest, DownloadStatus, Platform
from ...domain.repositories.download_request_repository import DownloadRequestRepository
from ...shared.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class JsonDownloadRequestRepository(DownloadRequestRepository):
    """JSON-based download request repository implementation"""
    
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
            logger.error(f"Failed to ensure download request file exists: {e}")
            raise RepositoryError(f"Failed to initialize download request repository: {e}")
    
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
            logger.error(f"Invalid JSON in download request repository: {e}")
            # Reset file if corrupted
            await self._write_data([])
            return []
        except Exception as e:
            logger.error(f"Error reading download request data: {e}")
            raise RepositoryError(f"Failed to read download request data: {e}")
    
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
            logger.error(f"Error writing download request data: {e}")
            raise RepositoryError(f"Failed to write download request data: {e}")
    
    def _request_to_dict(self, request: DownloadRequest) -> Dict[str, Any]:
        """Convert DownloadRequest entity to dictionary"""
        return {
            "id": request.id,
            "user_id": request.user_id,
            "url": request.url,
            "platform": request.platform.value if request.platform else None,
            "status": request.status.value,
            "created_at": request.created_at.isoformat() if request.created_at else None,
            "started_at": request.started_at.isoformat() if request.started_at else None,
            "completed_at": request.completed_at.isoformat() if request.completed_at else None,
            "error_message": request.error_message,
            "retry_count": request.retry_count,
            "max_retries": request.max_retries,
            "media_files": request.media_files,
            "metadata": request.metadata,
            "total_size": request.total_size,
            "processing_time": request.processing_time
        }
    
    def _dict_to_request(self, data: Dict[str, Any]) -> DownloadRequest:
        """Convert dictionary to DownloadRequest entity"""
        return DownloadRequest(
            id=data["id"],
            user_id=data["user_id"],
            url=data["url"],
            platform=Platform(data["platform"]) if data.get("platform") else None,
            status=DownloadStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            media_files=data.get("media_files", []),
            metadata=data.get("metadata", {}),
            total_size=data.get("total_size"),
            processing_time=data.get("processing_time")
        )
    
    async def save(self, request: DownloadRequest) -> DownloadRequest:
        """Save download request"""
        async with self._lock:
            try:
                data = await self._read_data()
                request_dict = self._request_to_dict(request)
                
                # Find existing request
                for i, existing in enumerate(data):
                    if existing["id"] == request.id:
                        data[i] = request_dict
                        break
                else:
                    # Request not found, add new
                    data.append(request_dict)
                
                await self._write_data(data)
                logger.debug(f"Saved download request {request.id}")
                return request
                
            except Exception as e:
                logger.error(f"Error saving download request {request.id}: {e}")
                raise RepositoryError(f"Failed to save download request: {e}")
    
    async def get_by_id(self, request_id: str) -> Optional[DownloadRequest]:
        """Get download request by ID"""
        try:
            data = await self._read_data()
            for request_dict in data:
                if request_dict["id"] == request_id:
                    return self._dict_to_request(request_dict)
            return None
        except Exception as e:
            logger.error(f"Error getting download request {request_id}: {e}")
            raise RepositoryError(f"Failed to get download request: {e}")
    
    async def get_by_user_id(self, user_id: int, limit: int = 50) -> List[DownloadRequest]:
        """Get download requests for a user"""
        try:
            data = await self._read_data()
            user_requests = []
            
            for request_dict in data:
                if request_dict["user_id"] == user_id:
                    user_requests.append(self._dict_to_request(request_dict))
            
            # Sort by created_at descending and limit
            user_requests.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
            return user_requests[:limit]
            
        except Exception as e:
            logger.error(f"Error getting download requests for user {user_id}: {e}")
            raise RepositoryError(f"Failed to get user download requests: {e}")
    
    async def get_pending_requests(self) -> List[DownloadRequest]:
        """Get all pending download requests"""
        try:
            data = await self._read_data()
            pending_requests = []
            
            for request_dict in data:
                if request_dict["status"] == DownloadStatus.PENDING.value:
                    pending_requests.append(self._dict_to_request(request_dict))
            
            # Sort by created_at ascending (oldest first)
            pending_requests.sort(key=lambda x: x.created_at or datetime.max)
            return pending_requests
            
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            raise RepositoryError(f"Failed to get pending requests: {e}")
    
    async def get_failed_requests(self, hours: int = 24) -> List[DownloadRequest]:
        """Get failed requests within specified hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            data = await self._read_data()
            failed_requests = []
            
            for request_dict in data:
                if request_dict["status"] == DownloadStatus.FAILED.value:
                    completed_at = datetime.fromisoformat(request_dict["completed_at"]) if request_dict.get("completed_at") else None
                    if completed_at and completed_at >= cutoff_time:
                        failed_requests.append(self._dict_to_request(request_dict))
            
            return failed_requests
            
        except Exception as e:
            logger.error(f"Error getting failed requests: {e}")
            raise RepositoryError(f"Failed to get failed requests: {e}")
    
    async def update_status(self, request_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update request status"""
        async with self._lock:
            try:
                data = await self._read_data()
                
                for request_dict in data:
                    if request_dict["id"] == request_id:
                        request_dict["status"] = status
                        if error_message:
                            request_dict["error_message"] = error_message
                        if status in [DownloadStatus.COMPLETED.value, DownloadStatus.FAILED.value, DownloadStatus.CANCELLED.value]:
                            request_dict["completed_at"] = datetime.now().isoformat()
                        elif status == DownloadStatus.PROCESSING.value:
                            request_dict["started_at"] = datetime.now().isoformat()
                        
                        await self._write_data(data)
                        logger.debug(f"Updated status for request {request_id} to {status}")
                        return True
                
                return False
                
            except Exception as e:
                logger.error(f"Error updating status for request {request_id}: {e}")
                raise RepositoryError(f"Failed to update request status: {e}")
    
    async def delete_old_requests(self, days: int = 7) -> int:
        """Delete old requests older than specified days"""
        async with self._lock:
            try:
                cutoff_date = datetime.now() - timedelta(days=days)
                data = await self._read_data()
                original_count = len(data)
                
                # Keep only requests newer than cutoff or still pending/processing
                filtered_data = []
                for request_dict in data:
                    created_at = datetime.fromisoformat(request_dict["created_at"]) if request_dict.get("created_at") else datetime.now()
                    status = request_dict.get("status")
                    
                    # Keep if recent, or if still pending/processing
                    if created_at >= cutoff_date or status in [DownloadStatus.PENDING.value, DownloadStatus.PROCESSING.value]:
                        filtered_data.append(request_dict)
                
                deleted_count = original_count - len(filtered_data)
                if deleted_count > 0:
                    await self._write_data(filtered_data)
                    logger.info(f"Deleted {deleted_count} old download requests")
                
                return deleted_count
                
            except Exception as e:
                logger.error(f"Error deleting old requests: {e}")
                raise RepositoryError(f"Failed to delete old requests: {e}")
    
    async def get_requests_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[DownloadRequest]:
        """Get requests within date range"""
        try:
            data = await self._read_data()
            requests_in_range = []
            
            for request_dict in data:
                created_at = datetime.fromisoformat(request_dict["created_at"]) if request_dict.get("created_at") else datetime.now()
                if start_date <= created_at <= end_date:
                    requests_in_range.append(self._dict_to_request(request_dict))
            
            # Sort by created_at
            requests_in_range.sort(key=lambda x: x.created_at or datetime.min)
            return requests_in_range
            
        except Exception as e:
            logger.error(f"Error getting requests by date range: {e}")
            raise RepositoryError(f"Failed to get requests by date range: {e}") 