# handlers/booking.py
"""
Обработчики для процесса записи на услуги
"""
import logging
from datetime import datetime, timedelta

from max_adapter import Router, F, Command, Message, CallbackQuery
from max_adapter import FSMContext, State, StateGroup
from keyboards.inline import (
    get_services_keyboard, get_masters_keyboard,
    get_calendar_keyboard, get_time_slots_keyboard,
    get_confirmation_keyboard, get_back_keyboard
)
from keyboards.reply import get_main_keyboard
from database.google_sheets import sheets_manager
from utils.helpers import validate_phone
from config import config

logger = logging.getLogger(__name__)

router = Router(name="booking")

# Состояния для FSM
class BookingStates(StateGroup):
    choosing_service = State()
    choosing_master = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    entering_phone = State()
    confirming = State()

@router.message(Command("book"))
async def cmd_book(message: Message, state: FSMContext):
    """Начало процесса записи"""
    await state.set_state(BookingStates.choosing_service)
    await message.answer(
        "Выберите услугу:",
        reply_markup=get_services_keyboard()
    )

@router.callback_query(BookingStates.choosing_service, F.data.startswith("service_"))
async def process_service(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора услуги"""
    await callback.answer()
    
    service = callback.data.replace("service_", "")
    await state.update_data(service=service)
    
    try:
        masters = sheets_manager.get_masters_by_service(service)
        
        if not masters:
            await callback.message.edit_text(
                "😔 К сожалению, нет мастеров для этой услуги. Выберите другую:",
                reply_markup=get_services_keyboard()
            )
            return
        
        await state.set_state(BookingStates.choosing_master)
        await callback.message.edit_text(
            "Выберите мастера:",
            reply_markup=get_masters_keyboard(masters)
        )
    except Exception as e:
        logger.error(f"Ошибка при получении мастеров: {e}")
        await callback.message.edit_text(
            "😔 Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

@router.callback_query(BookingStates.choosing_master, F.data.startswith("master_"))
async def process_master(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора мастера"""
    await callback.answer()
    
    master_id = callback.data.replace("master_", "")
    await state.update_data(master_id=master_id)
    
    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=get_calendar_keyboard()
    )

@router.callback_query(BookingStates.choosing_date, F.data.startswith("date_"))
async def process_date(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    await callback.answer()
    
    date = callback.data.replace("date_", "")
    await state.update_data(date=date)
    
    data = await state.get_data()
    try:
        slots = sheets_manager.get_available_slots(date, data['master_id'])
        
        if not slots:
            await callback.message.edit_text(
                "❌ На эту дату нет свободных слотов. Выберите другую дату:",
                reply_markup=get_calendar_keyboard()
            )
            return
        
        await state.set_state(BookingStates.choosing_time)
        await callback.message.edit_text(
            "Выберите время:",
            reply_markup=get_time_slots_keyboard(slots)
        )
    except Exception as e:
        logger.error(f"Ошибка при получении слотов: {e}")
        await callback.message.edit_text(
            "😔 Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

@router.callback_query(BookingStates.choosing_time, F.data.startswith("time_"))
async def process_time(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    await callback.answer()
    
    time = callback.data.replace("time_", "")
    await state.update_data(time=time)
    
    await state.set_state(BookingStates.entering_name)
    await callback.message.edit_text(
        "Введите ваше имя:"
    )

@router.message(BookingStates.entering_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка ввода имени"""
    name = message.text.strip()
    
    if len(name) < 2 or len(name) > 50:
        await message.answer(
            "❌ Имя должно быть от 2 до 50 символов. Попробуйте еще раз:"
        )
        return
    
    await state.update_data(client_name=name)
    await state.set_state(BookingStates.entering_phone)
    await message.answer(
        "Введите ваш номер телефона в формате +7XXXXXXXXXX:"
    )

@router.message(BookingStates.entering_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка ввода телефона"""
    phone = message.text.strip()
    
    if not validate_phone(phone):
        await message.answer(
            "❌ Неверный формат телефона. Введите в формате +7XXXXXXXXXX:"
        )
        return
    
    await state.update_data(client_phone=phone)
    
    data = await state.get_data()
    try:
        master = sheets_manager.get_master_by_id(data['master_id'])
        
        confirm_text = (
            f"📝 Проверьте данные записи:\n\n"
            f"👤 Имя: {data['client_name']}\n"
            f"📞 Телефон: {data['client_phone']}\n"
            f"💇 Услуга: {data['service']}\n"
            f"👩 Мастер: {master['name'] if master else 'Неизвестно'}\n"
            f"📅 Дата: {data['date']}\n"
            f"⏰ Время: {data['time']}\n\n"
            f"Всё верно?"
        )
        
        await state.set_state(BookingStates.confirming)
        await message.answer(
            confirm_text,
            reply_markup=get_confirmation_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при подтверждении: {e}")
        await message.answer(
            "😔 Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

@router.callback_query(BookingStates.confirming, F.data == "confirm")
async def process_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение записи"""
    await callback.answer()
    
    data = await state.get_data()
    
    try:
        success = sheets_manager.save_appointment(data)
        
        if success:
            await callback.message.edit_text(
                "✅ Запись подтверждена!\n\n"
                f"Ждем вас в салоне {config.SALON_NAME} в {data['date']} в {data['time']}.\n\n"
                f"Если появятся вопросы, звоните: {config.SALON_PHONE}"
            )
            
            await notify_admin(callback.message, data)
        else:
            await callback.message.edit_text(
                "❌ Ошибка при сохранении записи. Возможно, это время уже занято.\n"
                "Попробуйте выбрать другое время."
            )
    except Exception as e:
        logger.error(f"Ошибка при сохранении записи: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка. Попробуйте позже."
        )
    
    await state.clear()

@router.callback_query(BookingStates.confirming, F.data == "cancel")
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена записи"""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "❌ Запись отменена.",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "back")
async def process_back(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Назад'"""
    await callback.answer()
    
    current_state = await state.get_state()
    
    if current_state == BookingStates.choosing_master.state:
        await state.set_state(BookingStates.choosing_service)
        await callback.message.edit_text(
            "Выберите услугу:",
            reply_markup=get_services_keyboard()
        )
    elif current_state == BookingStates.choosing_date.state:
        await state.set_state(BookingStates.choosing_master)
        masters = sheets_manager.get_masters()
        await callback.message.edit_text(
            "Выберите мастера:",
            reply_markup=get_masters_keyboard(masters)
        )
    elif current_state == BookingStates.choosing_time.state:
        await state.set_state(BookingStates.choosing_date)
        await callback.message.edit_text(
            "Выберите дату:",
            reply_markup=get_calendar_keyboard()
        )
    elif current_state == BookingStates.confirming.state:
        await state.set_state(BookingStates.entering_phone)
        await callback.message.edit_text(
            "Введите ваш номер телефона:"
        )

async def notify_admin(message, data):
    """Отправка уведомления админу о новой записи"""
    if not config.ADMIN_IDS:
        return
    
    try:
        master = sheets_manager.get_master_by_id(data['master_id'])
        master_name = master['name'] if master else 'Неизвестно'
        
        admin_text = (
            f"📢 Новая запись!\n\n"
            f"👤 Клиент: {data['client_name']}\n"
            f"📞 Телефон: {data['client_phone']}\n"
            f"💇 Услуга: {data['service']}\n"
            f"👩 Мастер: {master_name}\n"
            f"📅 Дата: {data['date']}\n"
            f"⏰ Время: {data['time']}"
        )
        
        for admin_id in config.ADMIN_IDS:
            await message.bot.send_message(admin_id, admin_text)
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления админу: {e}")