"""
Translation system for DockShield
"""

import json
import locale
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class Translator:
    """Translation manager for multi-language support"""

    def __init__(self):
        """Initialize translator"""
        self.current_language = "en"
        self.translations: Dict[str, Dict[str, str]] = {}
        self.translations_dir = Path(__file__).parent.parent / "translations"

        # Load available translations
        self._load_translations()

    def _load_translations(self) -> None:
        """Load all available translation files"""
        if not self.translations_dir.exists():
            logger.warning(f"Translations directory not found: {self.translations_dir}")
            return

        for lang_file in self.translations_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                logger.info(f"Loaded translations for: {lang_code}")
            except Exception as e:
                logger.error(f"Error loading translations for {lang_code}: {e}")

    def set_language(self, lang_code: str) -> bool:
        """
        Set current language

        Args:
            lang_code: Language code (e.g., 'en', 'it')

        Returns:
            True if language was set successfully
        """
        if lang_code in self.translations:
            self.current_language = lang_code
            logger.info(f"Language set to: {lang_code}")
            return True
        else:
            logger.warning(f"Language not available: {lang_code}")
            return False

    def detect_system_language(self) -> str:
        """
        Detect system language

        Returns:
            Language code (e.g., 'en', 'it')
        """
        try:
            # Get system locale
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                # Extract language code (e.g., 'it_IT' -> 'it')
                lang_code = system_locale.split('_')[0].lower()

                # Check if we have translations for this language
                if lang_code in self.translations:
                    logger.info(f"Detected system language: {lang_code}")
                    return lang_code
                else:
                    logger.info(f"System language {lang_code} not supported, using English")
                    return "en"
            else:
                logger.info("Could not detect system language, using English")
                return "en"
        except Exception as e:
            logger.error(f"Error detecting system language: {e}")
            return "en"

    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get translated string

        Args:
            key: Translation key
            default: Default value if translation not found

        Returns:
            Translated string
        """
        if self.current_language in self.translations:
            translation = self.translations[self.current_language].get(key)
            if translation:
                return translation

        # Fallback to English
        if "en" in self.translations:
            translation = self.translations["en"].get(key)
            if translation:
                return translation

        # Return default or key itself
        return default if default is not None else key

    def get_available_languages(self) -> Dict[str, str]:
        """
        Get available languages

        Returns:
            Dictionary of language codes to language names
        """
        return {
            "en": "English",
            "it": "Italiano"
        }

    def get_current_language_name(self) -> str:
        """Get current language name"""
        languages = self.get_available_languages()
        return languages.get(self.current_language, "English")


# Global translator instance
_translator: Optional[Translator] = None


def get_translator() -> Translator:
    """Get global translator instance"""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def tr(key: str, default: Optional[str] = None) -> str:
    """
    Translate a string (shorthand function)

    Args:
        key: Translation key
        default: Default value if translation not found

    Returns:
        Translated string
    """
    return get_translator().get(key, default)
