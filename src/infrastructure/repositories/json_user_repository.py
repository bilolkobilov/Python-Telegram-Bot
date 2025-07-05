import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository
from ...shared.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class JsonUserRepository(UserRepository):
    """JSON-based user repository implementation"""
    
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
            logger.error(f"Failed to ensure file exists: {e}")
            raise RepositoryError(f"Failed to initialize user repository: {e}")
    
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
            logger.error(f"Invalid JSON in user repository: {e}")
            # Reset file if corrupted
            await self._write_data([])
            return []
        except Exception as e:
            logger.error(f"Error reading user data: {e}")
            raise RepositoryError(f"Failed to read user data: {e}")
    
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
            logger.error(f"Error writing user data: {e}")
            raise RepositoryError(f"Failed to write user data: {e}")
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert User entity to dictionary"""
        return {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language": user.language,
            "is_premium": user.is_premium,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_active": user.last_active.isoformat() if user.last_active else None,
            "download_count": user.download_count,
            "is_banned": user.is_banned
        }
    
    def _dict_to_user(self, data: Dict[str, Any]) -> User:
        """Convert dictionary to User entity"""
        return User(
            id=data["id"],
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            language=data.get("language", "en"),
            is_premium=data.get("is_premium", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            last_active=datetime.fromisoformat(data["last_active"]) if data.get("last_active") else None,
            download_count=data.get("download_count", 0),
            is_banned=data.get("is_banned", False)
        )
    
    async def save(self, user: User) -> User:
        """Save or update a user"""
        async with self._lock:
            try:
                data = await self._read_data()
                user_dict = self._user_to_dict(user)
                
                # Find existing user
                for i, existing in enumerate(data):
                    if existing["id"] == user.id:
                        data[i] = user_dict
                        break
                else:
                    # User not found, add new
                    data.append(user_dict)
                
                await self._write_data(data)
                logger.debug(f"Saved user {user.id}")
                return user
                
            except Exception as e:
                logger.error(f"Error saving user {user.id}: {e}")
                raise RepositoryError(f"Failed to save user: {e}")
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            data = await self._read_data()
            for user_dict in data:
                if user_dict["id"] == user_id:
                    return self._dict_to_user(user_dict)
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            raise RepositoryError(f"Failed to get user: {e}")
    
    async def get_all(self) -> List[User]:
        """Get all users"""
        try:
            data = await self._read_data()
            return [self._dict_to_user(user_dict) for user_dict in data]
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            raise RepositoryError(f"Failed to get all users: {e}")
    
    async def delete(self, user_id: int) -> bool:
        """Delete user by ID"""
        async with self._lock:
            try:
                data = await self._read_data()
                original_length = len(data)
                data = [user for user in data if user["id"] != user_id]
                
                if len(data) < original_length:
                    await self._write_data(data)
                    logger.debug(f"Deleted user {user_id}")
                    return True
                return False
                
            except Exception as e:
                logger.error(f"Error deleting user {user_id}: {e}")
                raise RepositoryError(f"Failed to delete user: {e}")
    
    async def exists(self, user_id: int) -> bool:
        """Check if user exists"""
        user = await self.get_by_id(user_id)
        return user is not None
    
    async def get_active_users(self, days: int = 30) -> List[User]:
        """Get users active within specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            data = await self._read_data()
            active_users = []
            
            for user_dict in data:
                if user_dict.get("last_active"):
                    last_active = datetime.fromisoformat(user_dict["last_active"])
                    if last_active >= cutoff_date:
                        active_users.append(self._dict_to_user(user_dict))
            
            return active_users
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            raise RepositoryError(f"Failed to get active users: {e}")
    
    async def get_banned_users(self) -> List[User]:
        """Get all banned users"""
        try:
            data = await self._read_data()
            banned_users = []
            
            for user_dict in data:
                if user_dict.get("is_banned", False):
                    banned_users.append(self._dict_to_user(user_dict))
            
            return banned_users
        except Exception as e:
            logger.error(f"Error getting banned users: {e}")
            raise RepositoryError(f"Failed to get banned users: {e}")
    
    async def count_total_users(self) -> int:
        """Get total user count"""
        try:
            data = await self._read_data()
            return len(data)
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            raise RepositoryError(f"Failed to count users: {e}") 