# keyboards/reply.py
"""
Обычные клавиатуры (ReplyKeyboardMarkup)
"""
from max_adapter import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    """Главное меню"""
    buttons = [
        [KeyboardButton(text="📅 Записаться")],
        [KeyboardButton(text="👩 Наши мастера")],
        [KeyboardButton(text="📞 Контакты")],
        [KeyboardButton(text="ℹ️ О нас")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_phone_keyboard():
    """Клавиатура для запроса номера телефона"""
    buttons = [
        [KeyboardButton(text="📱 Отправить номер", request_contact=True)],
        [KeyboardButton(text="◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    buttons = [
        [KeyboardButton(text="❌ Отменить запись")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )
