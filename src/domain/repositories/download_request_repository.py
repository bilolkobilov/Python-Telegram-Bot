from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from ..entities.download_request import DownloadRequest


class DownloadRequestRepository(ABC):
    """Abstract download request repository interface"""
    
    @abstractmethod
    async def save(self, request: DownloadRequest) -> DownloadRequest:
        """Save download request"""
        pass
    
    @abstractmethod
    async def get_by_id(self, request_id: str) -> Optional[DownloadRequest]:
        """Get download request by ID"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int, limit: int = 50) -> List[DownloadRequest]:
        """Get download requests for a user"""
        pass
    
    @abstractmethod
    async def get_pending_requests(self) -> List[DownloadRequest]:
        """Get all pending download requests"""
        pass
    
    @abstractmethod
    async def get_failed_requests(self, hours: int = 24) -> List[DownloadRequest]:
        """Get failed requests within specified hours"""
        pass
    
    @abstractmethod
    async def update_status(self, request_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update request status"""
        pass
    
    @abstractmethod
    async def delete_old_requests(self, days: int = 7) -> int:
        """Delete old requests older than specified days"""
        pass
    
    @abstractmethod
    async def get_requests_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[DownloadRequest]:
        """Get requests within date range"""
        pass