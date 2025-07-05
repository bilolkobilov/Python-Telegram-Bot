import asyncio
import logging
from typing import Optional, Dict, Any
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import TelegramError

from ...shared.config.settings import Settings
from ...shared.exceptions import MultisaveXException
from ...infrastructure.container import Container
from .handlers.command_handlers import CommandHandlers
from .handlers.message_handlers import MessageHandlers
from .handlers.callback_handlers import CallbackHandlers
from ...infrastructure.telegram.telegram_notification_service import TelegramNotificationService

logger = logging.getLogger(__name__)


class BotManager:
    """Telegram bot manager for handling bot lifecycle and routing"""
    
    def __init__(self, container: Container):
        self.container = container
        self.application: Optional[Application] = None
        self.admin_application: Optional[Application] = None
        self._is_running = False
        
        # Initialize handlers
        self.command_handlers = CommandHandlers(container)
        self.message_handlers = MessageHandlers(container)
        self.callback_handlers = CallbackHandlers(container)
    
    async def initialize(self):
        """Initialize the bot applications"""
        try:
            # Initialize container first
            await self.container.initialize()
            
            # Create main bot application
            self.application = (
                Application.builder()
                .token(Settings.BOT_TOKEN)
                .concurrent_updates(Settings.MAX_CONCURRENT_DOWNLOADS)
                .build()
            )
            
            # Create admin bot application if different token
            if Settings.ADMIN_BOT_TOKEN and Settings.ADMIN_BOT_TOKEN != Settings.BOT_TOKEN:
                self.admin_application = (
                    Application.builder()
                    .token(Settings.ADMIN_BOT_TOKEN)
                    .concurrent_updates(2)
                    .build()
                )
            
            # Setup notification service with bot instance
            notification_service = TelegramNotificationService(self.application.bot)
            self.container.set_notification_service(notification_service)
            
            # Register handlers
            await self._register_handlers()
            
            # Setup error handlers
            self._setup_error_handlers()
            
            logger.info("Bot manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot manager: {e}")
            raise MultisaveXException(f"Bot initialization failed: {e}")
    
    async def _register_handlers(self):
        """Register all bot handlers"""
        try:
            # Main bot handlers
            if self.application:
                app = self.application
                
                # Command handlers
                app.add_handler(CommandHandler("start", self.command_handlers.start_command))
                app.add_handler(CommandHandler("help", self.command_handlers.help_command))
                app.add_handler(CommandHandler("language", self.command_handlers.language_command))
                app.add_handler(CommandHandler("stats", self.command_handlers.stats_command))
                app.add_handler(CommandHandler("cancel", self.command_handlers.cancel_command))
                
                # Message handlers
                app.add_handler(MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    self.message_handlers.handle_text_message
                ))
                
                app.add_handler(MessageHandler(
                    filters.Document.ALL,
                    self.message_handlers.handle_document
                ))
                
                # Callback query handlers
                app.add_handler(CallbackQueryHandler(
                    self.callback_handlers.handle_callback_query
                ))
                
                # Fallback handler for unknown commands
                app.add_handler(MessageHandler(
                    filters.COMMAND,
                    self.command_handlers.unknown_command
                ))
            
            # Admin bot handlers (if separate)
            if self.admin_application:
                admin_app = self.admin_application
                
                # Admin command handlers
                admin_app.add_handler(CommandHandler("start", self.command_handlers.admin_start_command))
                admin_app.add_handler(CommandHandler("help", self.command_handlers.admin_help_command))
                admin_app.add_handler(CommandHandler("stats", self.command_handlers.admin_stats_command))
                admin_app.add_handler(CommandHandler("users", self.command_handlers.admin_users_command))
                admin_app.add_handler(CommandHandler("broadcast", self.command_handlers.admin_broadcast_command))
                admin_app.add_handler(CommandHandler("ban", self.command_handlers.admin_ban_command))
                admin_app.add_handler(CommandHandler("unban", self.command_handlers.admin_unban_command))
                admin_app.add_handler(CommandHandler("cleanup", self.command_handlers.admin_cleanup_command))
                
                # Admin callback handlers
                admin_app.add_handler(CallbackQueryHandler(
                    self.callback_handlers.handle_admin_callback_query
                ))
            
            logger.info("All handlers registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register handlers: {e}")
            raise MultisaveXException(f"Handler registration failed: {e}")
    
    def _setup_error_handlers(self):
        """Setup error handlers for the bot"""
        if self.application:
            self.application.add_error_handler(self._error_handler)
        
        if self.admin_application:
            self.admin_application.add_error_handler(self._admin_error_handler)
    
    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in main bot"""
        try:
            logger.error("Exception while handling an update:", exc_info=context.error)
            
            # Try to send error message to user if possible
            if isinstance(update, Update) and update.effective_chat:
                translation_service = self.container.get_translation_service()
                
                try:
                    # Get user language if possible
                    user_id = update.effective_user.id if update.effective_user else None
                    language = "en"
                    
                    if user_id:
                        user_repo = self.container.get_user_repository()
                        user = await user_repo.get_by_id(user_id)
                        if user:
                            language = user.language
                    
                    error_text = await translation_service.get_text("error_occurred", language)
                    
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=error_text
                    )
                    
                except Exception as send_error:
                    logger.error(f"Failed to send error message to user: {send_error}")
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    async def _admin_error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in admin bot"""
        try:
            logger.error("Exception in admin bot:", exc_info=context.error)
            
            # Send error message to admin
            if isinstance(update, Update) and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ Admin bot error: {str(context.error)[:200]}"
                )
                
        except Exception as e:
            logger.error(f"Error in admin error handler: {e}")
    
    async def start(self):
        """Start the bot applications"""
        try:
            if self._is_running:
                logger.warning("Bot manager is already running")
                return
            
            # Initialize if not already done
            if not self.application:
                await self.initialize()
            
            # Start main bot
            if self.application:
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )
                logger.info("Main bot started successfully")
            
            # Start admin bot if separate
            if self.admin_application:
                await self.admin_application.initialize()
                await self.admin_application.start()
                await self.admin_application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )
                logger.info("Admin bot started successfully")
            
            self._is_running = True
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info("Bot manager started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start bot manager: {e}")
            await self.stop()
            raise MultisaveXException(f"Bot startup failed: {e}")
    
    async def stop(self):
        """Stop the bot applications"""
        try:
            self._is_running = False
            
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Stop admin bot
            if self.admin_application:
                await self.admin_application.updater.stop()
                await self.admin_application.stop()
                await self.admin_application.shutdown()
                logger.info("Admin bot stopped")
            
            # Stop main bot
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Main bot stopped")
            
            logger.info("Bot manager stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bot manager: {e}")
    
    async def _start_background_tasks(self):
        """Start background maintenance tasks"""
        try:
            # Start cleanup task
            asyncio.create_task(self._cleanup_task())
            
            # Start rate limit cleanup task
            asyncio.create_task(self._rate_limit_cleanup_task())
            
            logger.info("Background tasks started")
            
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
    
    async def _stop_background_tasks(self):
        """Stop background tasks"""
        # Tasks will naturally stop when the event loop is closed
        # or when _is_running becomes False
        pass
    
    async def _cleanup_task(self):
        """Background task for cleaning up old data"""
        while self._is_running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Cleanup old download requests
                download_repo = self.container.get_download_request_repository()
                deleted_count = await download_repo.delete_old_requests(days=7)
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old download requests")
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _rate_limit_cleanup_task(self):
        """Background task for cleaning up expired rate limits"""
        while self._is_running:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                
                rate_limiter = self.container.get_rate_limiter_service()
                cleaned_count = await rate_limiter.cleanup_expired_limits()
                
                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} expired rate limit entries")
                
            except Exception as e:
                logger.error(f"Error in rate limit cleanup task: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    def is_running(self) -> bool:
        """Check if bot manager is running"""
        return self._is_running
    
    async def send_message_to_admins(self, message: str):
        """Send message to all admins"""
        if not self.application:
            return
        
        for admin_id in Settings.ADMIN_IDS:
            try:
                await self.application.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send message to admin {admin_id}: {e}")
    
    async def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information"""
        try:
            info = {}
            
            if self.application:
                bot_info = await self.application.bot.get_me()
                info["main_bot"] = {
                    "id": bot_info.id,
                    "username": bot_info.username,
                    "first_name": bot_info.first_name,
                    "can_join_groups": bot_info.can_join_groups,
                    "can_read_all_group_messages": bot_info.can_read_all_group_messages,
                    "supports_inline_queries": bot_info.supports_inline_queries
                }
            
            if self.admin_application:
                admin_bot_info = await self.admin_application.bot.get_me()
                info["admin_bot"] = {
                    "id": admin_bot_info.id,
                    "username": admin_bot_info.username,
                    "first_name": admin_bot_info.first_name
                }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return {}
    
    async def restart(self):
        """Restart the bot manager"""
        logger.info("Restarting bot manager...")
        await self.stop()
        await asyncio.sleep(2)
        await self.start()
        logger.info("Bot manager restarted") 