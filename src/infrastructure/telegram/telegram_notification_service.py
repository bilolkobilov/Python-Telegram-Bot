import asyncio
import logging
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import os

from ...application.interfaces.notification_service import NotificationService
from ...shared.exceptions import NotificationError
from ...shared.config.settings import Settings

logger = logging.getLogger(__name__)


class TelegramNotificationService(NotificationService):
    """Telegram notification service implementation"""
    
    def __init__(self, bot):
        self.bot = bot
        self._send_lock = asyncio.Semaphore(30) 
    
    async def send_message(
        self, 
        user_id: int, 
        text: str, 
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Any] = None,
        disable_web_page_preview: bool = False
    ) -> bool:
        """Send text message to user"""
        async with self._send_lock:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview
                )
                logger.debug(f"Sent message to user {user_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                return False
    
    async def send_media(
        self, 
        user_id: int, 
        file_path: str, 
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> bool:
        """Send media file to user"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            file_size = path.stat().st_size
            max_size = 50 * 1024 * 1024  # 50MB Telegram limit
            
            if file_size > max_size:
                logger.error(f"File too large to send: {file_size} bytes")
                return False
            
            # Determine media type based on extension
            extension = path.suffix.lower()
            
            if extension in ['.jpg', '.jpeg', '.png', '.webp']:
                return await self.send_photo(user_id, file_path, caption, parse_mode)
            elif extension in ['.mp4', '.mov', '.avi', '.mkv']:
                return await self.send_video(user_id, file_path, caption, parse_mode)
            else:
                return await self.send_document(user_id, file_path, caption, parse_mode)
                
        except Exception as e:
            logger.error(f"Failed to send media to user {user_id}: {e}")
            return False
    
    async def send_document(
        self, 
        user_id: int, 
        file_path: str, 
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> bool:
        """Send document to user"""
        async with self._send_lock:
            try:
                with open(file_path, 'rb') as file:
                    await self.bot.send_document(
                        chat_id=user_id,
                        document=file,
                        caption=caption,
                        parse_mode=parse_mode,
                        filename=Path(file_path).name
                    )
                logger.debug(f"Sent document to user {user_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to send document to user {user_id}: {e}")
                return False
    
    async def send_photo(
        self, 
        user_id: int, 
        file_path: str, 
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> bool:
        """Send photo to user"""
        async with self._send_lock:
            try:
                with open(file_path, 'rb') as photo:
                    await self.bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        caption=caption,
                        parse_mode=parse_mode
                    )
                logger.debug(f"Sent photo to user {user_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to send photo to user {user_id}: {e}")
                return False
    
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
        async with self._send_lock:
            try:
                with open(file_path, 'rb') as video:
                    await self.bot.send_video(
                        chat_id=user_id,
                        video=video,
                        caption=caption,
                        parse_mode=parse_mode,
                        duration=duration,
                        width=width,
                        height=height
                    )
                logger.debug(f"Sent video to user {user_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to send video to user {user_id}: {e}")
                return False
    
    async def edit_message(
        self, 
        user_id: int, 
        message_id: int, 
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """Edit existing message"""
        try:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            logger.debug(f"Edited message {message_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to edit message for user {user_id}: {e}")
            return False
    
    async def delete_message(self, user_id: int, message_id: int) -> bool:
        """Delete message"""
        try:
            await self.bot.delete_message(
                chat_id=user_id,
                message_id=message_id
            )
            logger.debug(f"Deleted message {message_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete message for user {user_id}: {e}")
            return False
    
    async def send_typing_action(self, user_id: int) -> bool:
        """Send typing action"""
        try:
            await self.bot.send_chat_action(
                chat_id=user_id,
                action="typing"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to send typing action to user {user_id}: {e}")
            return False
    
    async def send_upload_action(self, user_id: int, action: str = "upload_document") -> bool:
        """Send upload action (upload_photo, upload_video, upload_document)"""
        try:
            await self.bot.send_chat_action(
                chat_id=user_id,
                action=action
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to send upload action to user {user_id}: {e}")
            return False
    
    async def broadcast_message(
        self, 
        user_ids: List[int], 
        text: str,
        parse_mode: Optional[str] = None
    ) -> Dict[int, bool]:
        """Send message to multiple users"""
        results = {}
        
        # Send in batches to avoid overwhelming the API
        batch_size = 30
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            tasks = []
            
            for user_id in batch:
                task = self.send_message(user_id, text, parse_mode)
                tasks.append((user_id, task))
            
            # Wait for batch to complete
            for user_id, task in tasks:
                try:
                    result = await task
                    results[user_id] = result
                except Exception as e:
                    logger.error(f"Error in broadcast to user {user_id}: {e}")
                    results[user_id] = False
            
            # Small delay between batches
            if i + batch_size < len(user_ids):
                await asyncio.sleep(1)
        
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Broadcast completed: {successful}/{len(user_ids)} successful")
        
        return results
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information from Telegram"""
        try:
            chat = await self.bot.get_chat(user_id)
            
            return {
                "id": chat.id,
                "type": chat.type,
                "username": chat.username,
                "first_name": chat.first_name,
                "last_name": chat.last_name,
                "bio": getattr(chat, 'bio', None),
                "description": getattr(chat, 'description', None)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user info for {user_id}: {e}")
            return None
    
    async def send_media_group(
        self,
        user_id: int,
        file_paths: List[str],
        caption: Optional[str] = None
    ) -> bool:
        """Send multiple media files as a group"""
        try:
            if len(file_paths) > 10:
                logger.warning(f"Too many files in media group: {len(file_paths)}, limiting to 10")
                file_paths = file_paths[:10]
            
            media = []
            for i, file_path in enumerate(file_paths):
                path = Path(file_path)
                if not path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                extension = path.suffix.lower()
                
                with open(file_path, 'rb') as file:
                    if extension in ['.jpg', '.jpeg', '.png', '.webp']:
                        from telegram import InputMediaPhoto
                        media_item = InputMediaPhoto(
                            media=file.read(),
                            caption=caption if i == 0 else None
                        )
                    elif extension in ['.mp4', '.mov', '.avi', '.mkv']:
                        from telegram import InputMediaVideo
                        media_item = InputMediaVideo(
                            media=file.read(),
                            caption=caption if i == 0 else None
                        )
                    else:
                        continue  # Skip unsupported files
                    
                    media.append(media_item)
            
            if not media:
                logger.error("No valid media files found for group")
                return False
            
            await self.bot.send_media_group(
                chat_id=user_id,
                media=media
            )
            
            logger.debug(f"Sent media group with {len(media)} files to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send media group to user {user_id}: {e}")
            return False
    
    async def send_files_individually(
        self,
        user_id: int,
        file_paths: List[str],
        caption_template: Optional[str] = None
    ) -> List[bool]:
        """Send multiple files individually"""
        results = []
        
        for i, file_path in enumerate(file_paths):
            try:
                caption = None
                if caption_template:
                    caption = caption_template.format(
                        index=i + 1,
                        total=len(file_paths),
                        filename=Path(file_path).name
                    )
                
                result = await self.send_media(user_id, file_path, caption)
                results.append(result)
                
                # Small delay between files
                if i < len(file_paths) - 1:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Failed to send file {file_path} to user {user_id}: {e}")
                results.append(False)
        
        return results 