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

    # Complete response templates per language
    TEMPLATES = {
        'en': {
            # Basic responses
            'welcome': "Welcome! How can I help you today?",
            'select_cafe': "Please select a café from the list:",
            'which_one': "Which one would you like?",
            'business_welcome': "Welcome to {business_name}! How can I help you?",
            
            # Menu and ordering
            'menu_inquiry': "Here's our menu. What would you like?",
            'order_confirm': "Your order has been confirmed!",
            'order_help': "I can help you place an order. What would you like?",
            'no_menu': "Menu is not available right now.",
            
            # Booking and payment
            'booking_confirm': "Your table has been reserved!",
            'payment_request': "Your total is €{amount}. How would you like to pay?",
            'price_format': "€{amount}",
            
            # General responses
            'thank_you': "Thank you for your order!",
            'help': "I can help you with ordering, booking tables, or answering questions.",
            'hours_info': "We're open daily from 8 AM to 8 PM.",
            
            # Error and transfer messages
            'no_cafes': "No cafes are currently available. Please try again later.",
            'error': "Sorry, there was an error: {message}",
            'no_transfer': "Staff transfer not available on universal number.",
            'transferring': "Transferring you to our staff now. Please hold.",
            'transfer_failed': "Staff not available. Please try again later.",
            'contact_staff': "To speak with staff, please call {phone}."
        },
        'lv': {
            # Basic responses
            'welcome': "Laipni lūdzam! Kā varu jums palīdzēt?",
            'select_cafe': "Lūdzu, izvēlieties kafejnīcu no saraksta:",
            'which_one': "Kuru izvēlaties?",
            'business_welcome': "Laipni lūdzam {business_name}! Kā varu palīdzēt?",
            
            # Menu and ordering
            'menu_inquiry': "Šeit ir mūsu ēdienkarte. Ko vēlētos?",
            'order_confirm': "Jūsu pasūtījums ir apstiprināts!",
            'order_help': "Varu palīdzēt ar pasūtījumu. Ko vēlaties?",
            'no_menu': "Ēdienkarte šobrīd nav pieejama.",
            
            # Booking and payment
            'booking_confirm': "Jūsu galdiņš ir rezervēts!",
            'payment_request': "Kopā: €{amount}. Kā vēlaties maksāt?",
            'price_format': "€{amount}",
            
            # General responses
            'thank_you': "Paldies par jūsu pasūtījumu!",
            'help': "Varu palīdzēt ar pasūtījumiem, galdiņu rezervāciju vai atbildēt uz jautājumiem.",
            'hours_info': "Mēs esam atvērti katru dienu no 8:00 līdz 20:00.",
            
            # Error and transfer messages
            'no_cafes': "Kafejnīcas šobrīd nav pieejamas. Lūdzu, mēģiniet vēlāk.",
            'error': "Atvainojiet, radās kļūda: {message}",
            'no_transfer': "Personāla pārslēgšana nav pieejama universālajā numurā.",
            'transferring': "Pārslēdzu jūs uz mūsu personālu. Lūdzu, uzgaidiet.",
            'transfer_failed': "Personāls nav pieejams. Lūdzu, mēģiniet vēlāk.",
            'contact_staff': "Lai runātu ar personālu, lūdzu, zvaniet {phone}."
        },
        'ru': {
            # Basic responses
            'welcome': "Добро пожаловать! Чем могу помочь?",
            'select_cafe': "Пожалуйста, выберите кафе из списка:",
            'which_one': "Какое выберете?",
            'business_welcome': "Добро пожаловать в {business_name}! Чем могу помочь?",
            
            # Menu and ordering
            'menu_inquiry': "Вот наше меню. Что желаете?",
            'order_confirm': "Ваш заказ подтверждён!",
            'order_help': "Помогу сделать заказ. Что хотите?",
            'no_menu': "Меню сейчас недоступно.",
            
            # Booking and payment
            'booking_confirm': "Ваш столик забронирован!",
            'payment_request': "Итого: €{amount}. Как будете оплачивать?",
            'price_format': "€{amount}",
            
            # General responses
            'thank_you': "Спасибо за ваш заказ!",
            'help': "Могу помочь с заказами, бронированием столиков или ответить на вопросы.",
            'hours_info': "Мы работаем ежедневно с 8:00 до 20:00.",
            
            # Error and transfer messages
            'no_cafes': "Кафе сейчас недоступны. Попробуйте позже.",
            'error': "Извините, произошла ошибка: {message}",
            'no_transfer': "Перевод на персонал недоступен на универсальном номере.",
            'transferring': "Соединяю с нашим персоналом. Ожидайте.",
            'transfer_failed': "Персонал недоступен. Попробуйте позже.",
            'contact_staff': "Чтобы поговорить с персоналом, звоните {phone}."
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
        
        # If template not found in requested language, fallback to English
        if not template and language != 'en':
            template = self.TEMPLATES['en'].get(template_key, f"Template '{template_key}' not found")
        
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
            },
            'Coffee': {
                'lv': {'name': 'Kafija', 'description': 'Svaigi maltā kafija'},
                'ru': {'name': 'Кофе', 'description': 'Свежемолотый кофе'}
            },
            'Tea': {
                'lv': {'name': 'Tēja', 'description': 'Kvalitatīva tēja'},
                'ru': {'name': 'Чай', 'description': 'Качественный чай'}
            },
            'Sandwich': {
                'lv': {'name': 'Sviestmaize', 'description': 'Svaiga sviestmaize'},
                'ru': {'name': 'Сэндвич', 'description': 'Свежий сэндвич'}
            },
            'Cake': {
                'lv': {'name': 'Kūka', 'description': 'Mājas kūka'},
                'ru': {'name': 'Торт', 'description': 'Домашний торт'}
            }
        }

        if item_name in translations and target_language in translations[item_name]:
            return translations[item_name][target_language]

        # Return original if no translation available
        return {'name': item_name, 'description': item_description}