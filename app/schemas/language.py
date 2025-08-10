"""Language and localization schemas."""
from typing import Dict, Optional, List
from pydantic import BaseModel
from enum import Enum


class SupportedLanguage(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    LATVIAN = "lv"
    RUSSIAN = "ru"
    SPANISH = "es"
    FRENCH = "fr"


class LanguageDetectionResult(BaseModel):
    """Language detection result."""
    detected_language: SupportedLanguage
    confidence: float
    original_text: str


class TranslationRequest(BaseModel):
    """Translation request."""
    text: str
    source_language: Optional[SupportedLanguage] = None
    target_language: SupportedLanguage


class LocalizedContent(BaseModel):
    """Localized content for multiple languages."""
    content: Dict[str, str]  # {language_code: translated_text}

    class Config:
        json_schema_extra = {
            "example": {
                "content": {
                    "en": "Welcome to our café!",
                    "lv": "Laipni lūdzam mūsu kafejnīcā!",
                    "ru": "Добро пожаловать в наше кафе!"
                }
            }
        }


class MenuTranslation(BaseModel):
    """Menu item translation."""
    item_id: int
    translations: Dict[str, Dict[str, str]]  # {lang: {name, description}}

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": 1,
                "translations": {
                    "en": {"name": "Cappuccino", "description": "Rich espresso with foam"},
                    "lv": {"name": "Kapučīno", "description": "Bagāta espresso ar putām"},
                    "ru": {"name": "Капучино", "description": "Насыщенный эспрессо с пенкой"}
                }
            }
        }