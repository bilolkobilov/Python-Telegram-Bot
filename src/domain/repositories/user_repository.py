from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.user import User


class UserRepository(ABC):
    """Abstract user repository interface"""
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Save or update a user"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[User]:
        """Get all users"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Delete user by ID"""
        pass
    
    @abstractmethod
    async def exists(self, user_id: int) -> bool:
        """Check if user exists"""
        pass
    
    @abstractmethod
    async def get_active_users(self, days: int = 30) -> List[User]:
        """Get users active within specified days"""
        pass
    
    @abstractmethod
    async def get_banned_users(self) -> List[User]:
        """Get all banned users"""
        pass
    
    @abstractmethod
    async def count_total_users(self) -> int:
        """Get total user count"""
        pass