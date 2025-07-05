from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """User domain entity"""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: str = "en"
    is_premium: bool = False
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    download_count: int = 0
    is_banned: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_active is None:
            self.last_active = datetime.now()
    
    def update_activity(self):
        """Update user's last activity timestamp"""
        self.last_active = datetime.now()
    
    def increment_downloads(self):
        """Increment user's download count"""
        self.download_count += 1
        self.update_activity()
    
    def ban_user(self):
        """Ban the user"""
        self.is_banned = True
    
    def unban_user(self):
        """Unban the user"""
        self.is_banned = False
    
    def change_language(self, language: str):
        """Change user's language preference"""
        self.language = language
        self.update_activity()