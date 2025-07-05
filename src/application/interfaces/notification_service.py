from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from ...domain.entities.user import User
from ...domain.entities.media import Media


class NotificationService(ABC):
    """Abstract notification service interface"""
    
    @abstractmethod
    async def send_message(
        self, 
        user_id: int, 
        text: str, 
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Any] = None,
        disable_web_page_preview: bool = False
    ) -> bool:
        """Send text message to user"""
        pass
    
    @abstractmethod
    async def send_media(
        self, 
        user_id: int, 
        file_path: str, 
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> bool:
        """Send media file to user"""
        pass
    
    @abstractmethod
    async def send_document(
        self, 
        user_id: int, 
        file_path: str, 
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> bool:
        """Send document to user"""
        pass
    
    @abstractmethod
    async def send_photo(
        self, 
        user_id: int, 
        file_path: str, 
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> bool:
        """Send photo to user"""
        pass
    
    @abstractmethod
    async def send_video(
        self, 
        user_id: int, 
        file_path: str, 
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> bool:
        """Send video to user"""
        pass
    
    @abstractmethod
    async def edit_message(
        self, 
        user_id: int, 
        message_id: int, 
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """Edit existing message"""
        pass
    
    @abstractmethod
    async def delete_message(self, user_id: int, message_id: int) -> bool:
        """Delete message"""
        pass
    
    @abstractmethod
    async def send_typing_action(self, user_id: int) -> bool:
        """Send typing action"""
        pass
    
    @abstractmethod
    async def send_upload_action(self, user_id: int, action: str = "upload_document") -> bool:
        """Send upload action (upload_photo, upload_video, upload_document)"""
        pass
    
    @abstractmethod
    async def broadcast_message(
        self, 
        user_ids: List[int], 
        text: str,
        parse_mode: Optional[str] = None
    ) -> Dict[int, bool]:
        """Send message to multiple users"""
        pass
    
    @abstractmethod
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information from Telegram"""
        pass