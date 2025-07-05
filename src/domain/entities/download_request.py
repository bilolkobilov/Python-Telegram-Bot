from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

from .media import Media


class DownloadStatus(Enum):
    """Download request status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Platform(Enum):
    """Supported platform enumeration"""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


@dataclass
class DownloadRequest:
    """Download request domain entity"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int = 0
    url: str = ""
    platform: Optional[Platform] = None
    status: DownloadStatus = DownloadStatus.PENDING
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    media_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_size: Optional[int] = None
    processing_time: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # Determine platform from URL if not set
        if self.platform is None and self.url:
            if "instagram.com" in self.url or "instagr.am" in self.url:
                self.platform = Platform.INSTAGRAM
            elif "tiktok.com" in self.url or "vm.tiktok.com" in self.url:
                self.platform = Platform.TIKTOK
    
    def start_processing(self):
        """Mark request as started processing"""
        self.status = DownloadStatus.PROCESSING
        self.started_at = datetime.now()
    
    def complete_successfully(self, media_files: List[str], total_size: Optional[int] = None):
        """Mark request as completed successfully"""
        self.status = DownloadStatus.COMPLETED
        self.completed_at = datetime.now()
        self.media_files = media_files
        self.total_size = total_size
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def fail(self, error_message: str):
        """Mark request as failed"""
        self.status = DownloadStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def cancel(self):
        """Cancel the request"""
        self.status = DownloadStatus.CANCELLED
        self.completed_at = datetime.now()
        if self.started_at:
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def can_retry(self) -> bool:
        """Check if request can be retried"""
        return self.retry_count < self.max_retries and self.status == DownloadStatus.FAILED
    
    def increment_retry(self):
        """Increment retry count and reset to pending"""
        if self.can_retry():
            self.retry_count += 1
            self.status = DownloadStatus.PENDING
            self.error_message = None
            self.started_at = None
            self.completed_at = None
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the request"""
        self.metadata[key] = value
    
    def get_platform_name(self) -> str:
        """Get platform name as string"""
        return self.platform.value if self.platform else "unknown"
    
    def is_instagram(self) -> bool:
        """Check if this is an Instagram request"""
        return self.platform == Platform.INSTAGRAM
    
    def is_tiktok(self) -> bool:
        """Check if this is a TikTok request"""
        return self.platform == Platform.TIKTOK