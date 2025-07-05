import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import re

from ...application.interfaces.translation_service import TranslationService
from ...shared.exceptions import TranslationError
from ...shared.config.settings import Settings

logger = logging.getLogger(__name__)


class JsonTranslationService(TranslationService):
    """JSON-based translation service implementation"""
    
    def __init__(self, locales_dir: str):
        self.locales_dir = Path(locales_dir)
        self._translations: Dict[str, Dict[str, str]] = {}
        self._lock = asyncio.Lock()
        self._ensure_locales_exist()
    
    def _ensure_locales_exist(self):
        """Ensure locales directory and default translation files exist"""
        try:
            self.locales_dir.mkdir(parents=True, exist_ok=True)
            
            # Create default English translations if not exist
            en_file = self.locales_dir / "en.json"
            if not en_file.exists():
                self._create_default_translations(en_file, "en")
            
            # Create other language files if they don't exist
            for lang in Settings.SUPPORTED_LANGUAGES:
                lang_file = self.locales_dir / f"{lang}.json"
                if not lang_file.exists():
                    self._create_default_translations(lang_file, lang)
                    
        except Exception as e:
            logger.error(f"Failed to ensure locales exist: {e}")
            raise TranslationError(f"Failed to initialize translations: {e}")
    
    def _create_default_translations(self, file_path: Path, language: str):
        """Create default translation file for language"""
        default_translations = self._get_default_translations(language)
        
        try:
            content = json.dumps(default_translations, indent=2, ensure_ascii=False)
            file_path.write_text(content, encoding="utf-8")
            logger.info(f"Created default translations for {language}")
        except Exception as e:
            logger.error(f"Failed to create default translations for {language}: {e}")
    
    def _get_default_translations(self, language: str) -> Dict[str, str]:
        """Get default translations for a language"""
        translations = {
            "en": {
                # Bot commands
                "start": "🎉 Welcome to MultisaveX!\n\nI can help you download media from Instagram and TikTok. Just send me a link!",
                "help": "📖 **How to use MultisaveX:**\n\n• Send me an Instagram or TikTok link\n• I'll download and send you the media\n• Use /language to change language\n• Use /stats for your statistics",
                "language_changed": "✅ Language changed to English",
                "language_select": "🌍 **Select your language:**",
                
                # Download messages
                "processing": "⏳ Processing your request...",
                "downloading": "📥 Downloading media...",
                "download_success": "✅ Download completed! Sending files...",
                "download_failed": "❌ Failed to download media: {error}",
                "unsupported_url": "❌ This URL is not supported. Please send an Instagram or TikTok link.",
                "private_content": "🔒 This content is private or requires login.",
                "rate_limited": "⏰ You're doing that too fast. Please wait {time} before trying again.",
                "file_too_large": "📦 File is too large to send (max: {max_size}MB)",
                
                # User stats
                "user_stats": "📊 **Your Statistics:**\n\n👤 Downloads: {download_count}\n📅 Member since: {join_date}\n🌍 Language: {language}",
                
                # Admin commands
                "admin_help": "🔧 **Admin Commands:**\n\n/stats - System statistics\n/users - User management\n/broadcast - Send broadcast message\n/ban - Ban user\n/unban - Unban user",
                "system_stats": "📊 **System Statistics:**\n\n👥 Total users: {total_users}\n📥 Total downloads: {total_downloads}\n📈 Active users (30d): {active_users}\n🚫 Banned users: {banned_users}",
                "user_banned": "🚫 User {user_id} has been banned.",
                "user_unbanned": "✅ User {user_id} has been unbanned.",
                "broadcast_sent": "📢 Broadcast message sent to {count} users.",
                
                # Errors
                "error_occurred": "❌ An error occurred. Please try again later.",
                "not_authorized": "🔒 You are not authorized to use this command.",
                "user_banned_message": "🚫 You have been banned from using this bot.",
                
                # Buttons
                "button_download": "📥 Download",
                "button_cancel": "❌ Cancel",
                "button_retry": "🔄 Retry",
            },
            "ru": {
                # Bot commands
                "start": "🎉 Добро пожаловать в MultisaveX!\n\nЯ могу помочь вам скачать медиа из Instagram и TikTok. Просто отправьте мне ссылку!",
                "help": "📖 **Как использовать MultisaveX:**\n\n• Отправьте мне ссылку на Instagram или TikTok\n• Я скачаю и отправлю вам медиа\n• Используйте /language для смены языка\n• Используйте /stats для статистики",
                "language_changed": "✅ Язык изменен на русский",
                "language_select": "🌍 **Выберите ваш язык:**",
                
                # Download messages
                "processing": "⏳ Обрабатываю ваш запрос...",
                "downloading": "📥 Скачиваю медиа...",
                "download_success": "✅ Скачивание завершено! Отправляю файлы...",
                "download_failed": "❌ Не удалось скачать медиа: {error}",
                "unsupported_url": "❌ Эта ссылка не поддерживается. Пожалуйста, отправьте ссылку на Instagram или TikTok.",
                "private_content": "🔒 Этот контент приватный или требует авторизации.",
                "rate_limited": "⏰ Вы делаете это слишком быстро. Подождите {time} перед следующей попыткой.",
                "file_too_large": "📦 Файл слишком большой для отправки (макс: {max_size}МБ)",
                
                # User stats
                "user_stats": "📊 **Ваша статистика:**\n\n👤 Загрузок: {download_count}\n📅 Участник с: {join_date}\n🌍 Язык: {language}",
                
                # Admin commands
                "admin_help": "🔧 **Команды администратора:**\n\n/stats - Системная статистика\n/users - Управление пользователями\n/broadcast - Рассылка\n/ban - Заблокировать пользователя\n/unban - Разблокировать пользователя",
                "system_stats": "📊 **Системная статистика:**\n\n👥 Всего пользователей: {total_users}\n📥 Всего загрузок: {total_downloads}\n📈 Активных пользователей (30д): {active_users}\n🚫 Заблокированных: {banned_users}",
                "user_banned": "🚫 Пользователь {user_id} заблокирован.",
                "user_unbanned": "✅ Пользователь {user_id} разблокирован.",
                "broadcast_sent": "📢 Сообщение разослано {count} пользователям.",
                
                # Errors
                "error_occurred": "❌ Произошла ошибка. Попробуйте позже.",
                "not_authorized": "🔒 У вас нет прав для использования этой команды.",
                "user_banned_message": "🚫 Вы заблокированы в этом боте.",
                
                # Buttons
                "button_download": "📥 Скачать",
                "button_cancel": "❌ Отмена",
                "button_retry": "🔄 Повторить",
            },
            "uz": {
                # Bot commands
                "start": "🎉 MultisaveX botiga xush kelibsiz!\n\nMen sizga Instagram va TikTok'dan media yuklab olishda yordam bera olaman. Shunchaki menga havola yuboring!",
                "help": "📖 **MultisaveX'dan qanday foydalanish:**\n\n• Menga Instagram yoki TikTok havolasini yuboring\n• Men mediani yuklab olib, sizga yuboraman\n• Tilni o'zgartirish uchun /language ni ishlating\n• Statistika uchun /stats ni ishlating",
                "language_changed": "✅ Til o'zbek tiliga o'zgartirildi",
                "language_select": "🌍 **Tilingizni tanlang:**",
                
                # Download messages
                "processing": "⏳ So'rovingizni qayta ishlamoqdaman...",
                "downloading": "📥 Media yuklamoqdaman...",
                "download_success": "✅ Yuklash yakunlandi! Fayllarni yubormoqdaman...",
                "download_failed": "❌ Mediani yuklab olmadim: {error}",
                "unsupported_url": "❌ Bu havola qo'llab-quvvatlanmaydi. Iltimos, Instagram yoki TikTok havolasini yuboring.",
                "private_content": "🔒 Bu kontent shaxsiy yoki kirish talab qiladi.",
                "rate_limited": "⏰ Siz buni juda tez qilyapsiz. Iltimos, {time} kuting.",
                "file_too_large": "📦 Fayl yuborish uchun juda katta (maks: {max_size}MB)",
                
                # User stats
                "user_stats": "📊 **Sizning statistikangiz:**\n\n👤 Yuklamalar: {download_count}\n📅 A'zo bo'lgan sana: {join_date}\n🌍 Til: {language}",
                
                # Admin commands
                "admin_help": "🔧 **Admin buyruqlari:**\n\n/stats - Tizim statistikasi\n/users - Foydalanuvchilarni boshqarish\n/broadcast - Umumiy xabar yuborish\n/ban - Foydalanuvchini bloklash\n/unban - Foydalanuvchini blokdan chiqarish",
                "system_stats": "📊 **Tizim statistikasi:**\n\n👥 Jami foydalanuvchilar: {total_users}\n📥 Jami yuklamalar: {total_downloads}\n📈 Faol foydalanuvchilar (30k): {active_users}\n🚫 Bloklangan: {banned_users}",
                "user_banned": "🚫 Foydalanuvchi {user_id} bloklandi.",
                "user_unbanned": "✅ Foydalanuvchi {user_id} blokdan chiqarildi.",
                "broadcast_sent": "📢 Xabar {count} foydalanuvchiga yuborildi.",
                
                # Errors
                "error_occurred": "❌ Xatolik yuz berdi. Keyinroq qayta urinib ko'ring.",
                "not_authorized": "🔒 Sizda bu buyruqni ishlatish huquqi yo'q.",
                "user_banned_message": "🚫 Siz ushbu botda bloklangansiez.",
                
                # Buttons
                "button_download": "📥 Yuklash",
                "button_cancel": "❌ Bekor qilish",
                "button_retry": "🔄 Qayta urinish",
            }
        }
        
        return translations.get(language, translations["en"])
    
    async def _load_language(self, language: str) -> bool:
        """Load translations for a specific language"""
        try:
            lang_file = self.locales_dir / f"{language}.json"
            if not lang_file.exists():
                logger.warning(f"Translation file not found for language: {language}")
                return False
            
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                lambda: lang_file.read_text(encoding="utf-8")
            )
            
            translations = json.loads(content)
            async with self._lock:
                self._translations[language] = translations
            
            logger.debug(f"Loaded {len(translations)} translations for language: {language}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading translations for {language}: {e}")
            return False
    
    async def get_text(
        self, 
        key: str, 
        language: str = "en", 
        **kwargs: Any
    ) -> str:
        """Get translated text for key in specified language"""
        try:
            # Ensure language is supported
            if language not in Settings.SUPPORTED_LANGUAGES:
                language = Settings.DEFAULT_LANGUAGE
            
            # Load language if not already loaded
            if language not in self._translations:
                await self._load_language(language)
            
            # Get translation
            translations = self._translations.get(language, {})
            text = translations.get(key)
            
            # Fallback to English if not found
            if text is None and language != "en":
                if "en" not in self._translations:
                    await self._load_language("en")
                text = self._translations.get("en", {}).get(key)
            
            # Fallback to key if still not found
            if text is None:
                logger.warning(f"Translation not found for key '{key}' in language '{language}'")
                text = key
            
            # Format text with provided kwargs
            if kwargs:
                try:
                    text = text.format(**kwargs)
                except KeyError as e:
                    logger.warning(f"Missing format parameter {e} for key '{key}'")
                except Exception as e:
                    logger.error(f"Error formatting text for key '{key}': {e}")
            
            return text
            
        except Exception as e:
            logger.error(f"Error getting translation for key '{key}': {e}")
            return key  # Return key as fallback
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return Settings.SUPPORTED_LANGUAGES.copy()
    
    async def is_language_supported(self, language: str) -> bool:
        """Check if language is supported"""
        return language in Settings.SUPPORTED_LANGUAGES
    
    async def get_language_name(self, language_code: str, in_language: str = "en") -> str:
        """Get language name in specified language"""
        language_names = {
            "en": {"en": "English", "ru": "Russian", "uz": "Uzbek"},
            "ru": {"en": "Английский", "ru": "Русский", "uz": "Узбекский"},
            "uz": {"en": "Inglizcha", "ru": "Ruscha", "uz": "O'zbekcha"}
        }
        
        names = language_names.get(in_language, language_names["en"])
        return names.get(language_code, language_code)
    
    async def detect_language_from_text(self, text: str) -> Optional[str]:
        """Detect language from text (basic implementation)"""
        # Simple detection based on character patterns
        if re.search(r'[а-яё]', text.lower()):
            return "ru"
        elif re.search(r'[ўқғҳ]', text.lower()):
            return "uz"
        else:
            return "en"
    
    async def get_all_translations(self, language: str = "en") -> Dict[str, str]:
        """Get all translations for a language"""
        try:
            if language not in self._translations:
                await self._load_language(language)
            
            return self._translations.get(language, {}).copy()
            
        except Exception as e:
            logger.error(f"Error getting all translations for {language}: {e}")
            return {}
    
    async def reload_translations(self) -> bool:
        """Reload translations from files"""
        try:
            async with self._lock:
                self._translations.clear()
            
            # Reload all supported languages
            for language in Settings.SUPPORTED_LANGUAGES:
                await self._load_language(language)
            
            logger.info("Reloaded all translations")
            return True
            
        except Exception as e:
            logger.error(f"Error reloading translations: {e}")
            return False
    
    async def add_translation(
        self, 
        key: str, 
        language: str, 
        text: str
    ) -> bool:
        """Add or update translation"""
        try:
            if language not in Settings.SUPPORTED_LANGUAGES:
                return False
            
            # Load language if not already loaded
            if language not in self._translations:
                await self._load_language(language)
            
            # Update translation in memory
            async with self._lock:
                if language not in self._translations:
                    self._translations[language] = {}
                self._translations[language][key] = text
            
            # Save to file
            lang_file = self.locales_dir / f"{language}.json"
            loop = asyncio.get_event_loop()
            content = json.dumps(self._translations[language], indent=2, ensure_ascii=False)
            await loop.run_in_executor(
                None,
                lambda: lang_file.write_text(content, encoding="utf-8")
            )
            
            logger.debug(f"Added translation for key '{key}' in language '{language}'")
            return True
            
        except Exception as e:
            logger.error(f"Error adding translation for key '{key}': {e}")
            return False
    
    async def get_missing_translations(self, reference_language: str = "en") -> Dict[str, List[str]]:
        """Get missing translations for each language compared to reference"""
        try:
            # Load reference language
            if reference_language not in self._translations:
                await self._load_language(reference_language)
            
            reference_keys = set(self._translations.get(reference_language, {}).keys())
            missing = {}
            
            for language in Settings.SUPPORTED_LANGUAGES:
                if language == reference_language:
                    continue
                
                # Load language if not already loaded
                if language not in self._translations:
                    await self._load_language(language)
                
                language_keys = set(self._translations.get(language, {}).keys())
                missing_keys = reference_keys - language_keys
                
                if missing_keys:
                    missing[language] = list(missing_keys)
            
            return missing
            
        except Exception as e:
            logger.error(f"Error getting missing translations: {e}")
            return {} 