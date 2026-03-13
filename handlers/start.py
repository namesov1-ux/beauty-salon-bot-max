# handlers/start.py
"""
Обработчики для команды /start и главного меню
"""
import logging
from datetime import datetime

from max_adapter import Router, Command, Message, FSMContext
from keyboards.reply import get_main_keyboard
from config import config
from database.google_sheets import sheets_manager

logger = logging.getLogger(__name__)

router = Router(name="start")

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    # Очищаем состояние пользователя
    await state.clear()
    
    # Получаем информацию о пользователе
    user = message.from_user
    logger.info(f"Пользователь {user.id} (@{user.username}) запустил бота")
    
    # Формируем приветственное сообщение
    welcome_text = (
        f"👋 Добро пожаловать в салон {config.SALON_NAME}!\n\n"
        f"Я помогу вам записаться на услуги, выбрать мастера и узнать информацию о салоне.\n\n"
        f"📋 Что я умею:\n"
        f"📅 Записаться на услугу\n"
        f"👩 Посмотреть список мастеров\n"
        f"📞 Узнать контакты салона\n"
        f"ℹ️ Информацию о нас\n\n"
        f"Выберите действие в меню ниже:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

@router.message(lambda message: message.text == "📅 Записаться")
async def book_service(message: Message, state: FSMContext):
    """Обработчик кнопки 'Записаться'"""
    from handlers.booking import cmd_book
    await cmd_book(message, state)

@router.message(lambda message: message.text == "👩 Наши мастера")
async def show_masters(message: Message, state: FSMContext):
    """Показать список мастеров"""
    try:
        masters = sheets_manager.get_masters()
        
        if not masters:
            await message.answer(
                "😔 Информация о мастерах временно недоступна.",
                reply_markup=get_main_keyboard()
            )
            return
        
        text = "👩 Наши мастера:\n\n"
        for master in masters:
            text += (
                f"✨ {master['name']}\n"
                f"💇 Специализация: {master['specialization']}\n"
                f"⏰ Опыт: {master['experience']}\n"
                f"🕐 Часы работы: {master['working_hours']}\n\n"
            )
        
        await message.answer(
            text,
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка мастеров: {e}")
        await message.answer(
            "😔 Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )

@router.message(lambda message: message.text == "📞 Контакты")
async def show_contacts(message: Message, state: FSMContext):
    """Показать контакты салона"""
    contacts_text = (
        f"📞 Контакты салона {config.SALON_NAME}:\n\n"
        f"📍 Адрес: {config.SALON_ADDRESS}\n"
        f"📱 Телефон: {config.SALON_PHONE}\n"
        f"📷 Instagram: {config.SALON_INSTAGRAM}\n\n"
        f"🕐 Часы работы:\n"
        f"Будни: {config.WORK_HOURS_WEEKDAYS}\n"
        f"Выходные: {config.WORK_HOURS_WEEKEND}"
    )
    
    await message.answer(
        contacts_text,
        reply_markup=get_main_keyboard()
    )

@router.message(lambda message: message.text == "ℹ️ О нас")
async def show_about(message: Message, state: FSMContext):
    """Показать информацию о салоне"""
    about_text = (
        f"ℹ️ О салоне {config.SALON_NAME}\n\n"
        f"Мы - команда профессионалов с многолетним опытом.\n"
        f"Используем только качественные материалы и следим за новинками в индустрии красоты.\n\n"
        f"✨ Наши преимущества:\n"
        f"✅ Опытные мастера\n"
        f"✅ Современное оборудование\n"
        f"✅ Индивидуальный подход\n"
        f"✅ Доступные цены\n"
        f"✅ Уютная атмосфера\n\n"
        f"Ждем вас в нашем салоне!"
    )
    
    await message.answer(
        about_text,
        reply_markup=get_main_keyboard()
    )

@router.message()
async def handle_unknown(message: Message, state: FSMContext):
    """Обработчик неизвестных команд"""
    await message.answer(
        "Я не понимаю эту команду. Пожалуйста, используйте меню.",
        reply_markup=get_main_keyboard()
    )