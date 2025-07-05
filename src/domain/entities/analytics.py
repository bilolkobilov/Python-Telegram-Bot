from dataclasses import dataclass
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum


class AnalyticsEventType(Enum):
    """Analytics event type enumeration"""
    DOWNLOAD_START = "download_start"
    DOWNLOAD_SUCCESS = "download_success"
    DOWNLOAD_FAILED = "download_failed"
    USER_JOINED = "user_joined"
    USER_BANNED = "user_banned"
    COMMAND_USED = "command_used"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Analytics:
    """Analytics domain entity for tracking user behavior and system performance"""
    id: str
    user_id: int
    event_type: AnalyticsEventType
    platform: Optional[str] = None  # instagram, tiktok
    media_type: Optional[str] = None  # image, video, reel, etc.
    url: Optional[str] = None
    file_size: Optional[int] = None
    processing_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the analytics record"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def mark_as_failed(self, error_message: str):
        """Mark the analytics record as failed"""
        self.success = False
        self.error_message = error_message
    
    def set_processing_time(self, start_time: datetime):
        """Set processing time based on start time"""
        self.processing_time = (datetime.now() - start_time).total_seconds()
    
    def is_download_event(self) -> bool:
        """Check if this is a download-related event"""
        return self.event_type in [
            AnalyticsEventType.DOWNLOAD_START,
            AnalyticsEventType.DOWNLOAD_SUCCESS,
            AnalyticsEventType.DOWNLOAD_FAILED
        ]