from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class TranslationService(ABC):
    """Abstract translation service interface"""
    
    @abstractmethod
    async def get_text(
        self, 
        key: str, 
        language: str = "en", 
        **kwargs: Any
    ) -> str:
        """
        Get translated text for key in specified language
        
        Args:
            key: Translation key
            language: Language code (en, ru, uz, etc.)
            **kwargs: Variables for string formatting
            
        Returns:
            Translated text with variables substituted
        """
        pass
    
    @abstractmethod
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        pass
    
    @abstractmethod
    async def is_language_supported(self, language: str) -> bool:
        """Check if language is supported"""
        pass
    
    @abstractmethod
    async def get_language_name(self, language_code: str, in_language: str = "en") -> str:
        """Get language name in specified language"""
        pass
    
    @abstractmethod
    async def detect_language_from_text(self, text: str) -> Optional[str]:
        """Detect language from text (if supported)"""
        pass
    
    @abstractmethod
    async def get_all_translations(self, language: str = "en") -> Dict[str, str]:
        """Get all translations for a language"""
        pass
    
    @abstractmethod
    async def reload_translations(self) -> bool:
        """Reload translations from files"""
        pass
    
    @abstractmethod
    async def add_translation(
        self, 
        key: str, 
        language: str, 
        text: str
    ) -> bool:
        """Add or update translation"""
        pass
    
    @abstractmethod
    async def get_missing_translations(self, reference_language: str = "en") -> Dict[str, List[str]]:
        """Get missing translations for each language compared to reference"""
        pass