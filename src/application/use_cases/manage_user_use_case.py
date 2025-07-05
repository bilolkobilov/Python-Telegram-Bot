from typing import Optional
from datetime import datetime

from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository
from ..interfaces.notification_service import NotificationService
from ..interfaces.translation_service import TranslationService


class ManageUserUseCase:
    """Use case for managing users"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        notification_service: Optional[NotificationService],
        translation_service: TranslationService
    ):
        self.user_repository = user_repository
        self.notification_service: Optional[NotificationService] = notification_service
        self.translation_service = translation_service
    
    async def register_user(
        self, 
        user_id: int, 
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: str = "en"
    ) -> User:
        """Register a new user"""
        # Check if user already exists
        existing_user = await self.user_repository.get_by_id(user_id)
        if existing_user:
            # Update existing user info
            existing_user.username = username
            existing_user.first_name = first_name
            existing_user.last_name = last_name
            existing_user.update_activity()
            return await self.user_repository.update(existing_user)
        
        # Create new user
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language
        )
        
        user = await self.user_repository.create(user)
        
        # Send welcome message
        welcome_message = await self.translation_service.get_translation(
            language, "welcome_message", name=first_name or username or "User"
        )
        await self.notification_service.send_message(user_id, welcome_message)
        
        return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await self.user_repository.get_by_id(user_id)
    
    async def update_user_language(self, user_id: int, language: str) -> User:
        """Update user language"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.change_language(language)
        user = await self.user_repository.update(user)
        
        # Send confirmation message
        confirmation_message = await self.translation_service.get_translation(
            language, "language_changed"
        )
        await self.notification_service.send_message(user_id, confirmation_message)
        
        return user
    
    async def ban_user(self, user_id: int, admin_id: int) -> User:
        """Ban a user"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.ban_user()
        user = await self.user_repository.update(user)
        
        # Send ban notification
        ban_message = await self.translation_service.get_translation(
            user.language, "user_banned"
        )
        await self.notification_service.send_message(user_id, ban_message)
        
        return user
    
    async def unban_user(self, user_id: int, admin_id: int) -> User:
        """Unban a user"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.unban_user()
        user = await self.user_repository.update(user)
        
        # Send unban notification
        unban_message = await self.translation_service.get_translation(
            user.language, "user_unbanned"
        )
        await self.notification_service.send_message(user_id, unban_message)
        
        return user
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        return await self.user_repository.delete(user_id)