from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from datetime import datetime


class MediaType(Enum):
    """Media type enumeration"""
    IMAGE = "image"
    VIDEO = "video"
    STORY = "story"
    HIGHLIGHT = "highlight"
    REEL = "reel"
    TIKTOK_VIDEO = "tiktok_video"


@dataclass
class Media:
    """Media domain entity"""
    id: str
    url: str
    media_type: MediaType
    platform: str  # instagram, tiktok
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def is_video(self) -> bool:
        """Check if media is a video type"""
        return self.media_type in [MediaType.VIDEO, MediaType.REEL, MediaType.TIKTOK_VIDEO]
    
    def is_image(self) -> bool:
        """Check if media is an image type"""
        return self.media_type == MediaType.IMAGE
    
    def is_story_content(self) -> bool:
        """Check if media is story content"""
        return self.media_type in [MediaType.STORY, MediaType.HIGHLIGHT]
    
    def get_file_extension(self) -> str:
        """Get appropriate file extension based on media type"""
        if self.is_video():
            return ".mp4"
        elif self.is_image():
            return ".jpg"
        return ".bin"