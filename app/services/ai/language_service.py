"""Language detection and translation service."""
from typing import Optional, Dict, List
import langdetect
from app.schemas.language import (
    SupportedLanguage,
    LanguageDetectionResult,
    LocalizedContent
)


class LanguageService:
    """Handle language detection and localization."""

    # Language patterns for intent detection
    LANGUAGE_PATTERNS = {
        'lv': {
            'greeting': ['labdien', 'sveiki', 'čau', 'labrīt', 'labvakar'],
            'menu': ['ēdienkarte', 'izvēlne', 'menu'],
            'order': ['pasūtīt', 'vēlos', 'gribu', 'lūdzu'],
            'booking': ['rezervēt', 'galdiņš', 'rezervācija'],
            'payment': ['maksāt', 'rēķins', 'cena'],
            'help': ['palīdzība', 'palīdzi', 'nesaprotu']
        },
        'ru': {
            'greeting': ['привет', 'здравствуйте', 'добрый день', 'добрый вечер'],
            'menu': ['меню', 'блюда', 'напитки'],
            'order': ['заказать', 'хочу', 'буду', 'пожалуйста'],
            'booking': ['забронировать', 'столик', 'резерв'],
            'payment': ['оплатить', 'счёт', 'цена'],
            'help': ['помощь', 'помогите', 'не понимаю']
        }
    }

    # Response templates per language
    TEMPLATES = {
        'en': {
            'welcome': "Welcome! How can I help you today?",
            'select_cafe': "Please select a café from the list:",
            'menu_inquiry': "Here's our menu. What would you like?",
            'order_confirm': "Your order has been confirmed!",
            'booking_confirm': "Your table has been reserved!",
            'payment_request': "Your total is €{amount}. How would you like to pay?",
            'thank_you': "Thank you for your order!",
            'help': "I can help you with ordering, booking tables, or answering questions."
        },
        'lv': {
            'welcome': "Laipni lūdzam! Kā varu jums palīdzēt?",
            'select_cafe': "Lūdzu, izvēlieties kafejnīcu no saraksta:",
            'menu_inquiry': "Šeit ir mūsu ēdienkarte. Ko vēlētos?",
            'order_confirm': "Jūsu pasūtījums ir apstiprināts!",
            'booking_confirm': "Jūsu galdiņš ir rezervēts!",
            'payment_request': "Kopā: €{amount}. Kā vēlaties maksāt?",
            'thank_you': "Paldies par jūsu pasūtījumu!",
            'help': "Varu palīdzēt ar pasūtījumiem, galdiņu rezervāciju vai atbildēt uz jautājumiem."
        },
        'ru': {
            'welcome': "Добро пожаловать! Чем могу помочь?",
            'select_cafe': "Пожалуйста, выберите кафе из списка:",
            'menu_inquiry': "Вот наше меню. Что желаете?",
            'order_confirm': "Ваш заказ подтверждён!",
            'booking_confirm': "Ваш столик забронирован!",
            'payment_request': "Итого: €{amount}. Как будете оплачивать?",
            'thank_you': "Спасибо за ваш заказ!",
            'help': "Могу помочь с заказами, бронированием столиков или ответить на вопросы."
        }
    }

    def detect_language(self, text: str) -> LanguageDetectionResult:
        """Detect language from text."""
        try:
            detected = langdetect.detect(text)
            confidence = langdetect.detect_langs(text)[0].prob

            # Map to our supported languages
            lang_map = {
                'en': SupportedLanguage.ENGLISH,
                'lv': SupportedLanguage.LATVIAN,
                'ru': SupportedLanguage.RUSSIAN,
                'es': SupportedLanguage.SPANISH,
                'fr': SupportedLanguage.FRENCH
            }

            language = lang_map.get(detected, SupportedLanguage.ENGLISH)

            return LanguageDetectionResult(
                detected_language=language,
                confidence=confidence,
                original_text=text
            )
        except:
            # Default to English if detection fails
            return LanguageDetectionResult(
                detected_language=SupportedLanguage.ENGLISH,
                confidence=0.5,
                original_text=text
            )

    def get_template(self, language: str, template_key: str, **kwargs) -> str:
        """Get localized template with variables."""
        templates = self.TEMPLATES.get(language, self.TEMPLATES['en'])
        template = templates.get(template_key, "")
        return template.format(**kwargs) if kwargs else template

    def translate_menu_item(
        self,
        item_name: str,
        item_description: str,
        target_language: str
    ) -> Dict[str, str]:
        """Translate menu item (placeholder for real translation API)."""

        # In production, integrate with Google Translate or DeepL
        # For now, return predefined translations for common items

        translations = {
            'Cappuccino': {
                'lv': {'name': 'Kapučīno', 'description': 'Espresso ar piena putām'},
                'ru': {'name': 'Капучино', 'description': 'Эспрессо с молочной пенкой'}
            },
            'Latte': {
                'lv': {'name': 'Latte', 'description': 'Maigs espresso ar pienu'},
                'ru': {'name': 'Латте', 'description': 'Мягкий эспрессо с молоком'}
            }
        }

        if item_name in translations and target_language in translations[item_name]:
            return translations[item_name][target_language]

        # Return original if no translation available
        return {'name': item_name, 'description': item_description}