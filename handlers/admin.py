# handlers/admin.py
"""
Обработчики для администраторов салона
"""
import logging
from datetime import datetime, timedelta

from max_adapter import Router, F, Command, Message, CallbackQuery, FSMContext
from keyboards.admin import get_admin_keyboard, get_admin_actions_keyboard
from keyboards.reply import get_main_keyboard
from database.google_sheets import sheets_manager
from config import config

logger = logging.getLogger(__name__)

router = Router(name="admin")

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in config.ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    """Админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return
    
    await state.clear()
    
    admin_text = (
        "👑 Административная панель\n\n"
        "Выберите действие:"
    )
    
    await message.answer(
        admin_text,
        reply_markup=get_admin_keyboard()
    )

@router.message(Command("today"))
async def admin_today(message: Message):
    """Записи на сегодня (быстрая команда)"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    
    await show_today_appointments(message)

@router.message(Command("stats"))
async def admin_stats(message: Message):
    """Статистика записей"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    
    await show_statistics(message)

@router.message(Command("masters"))
async def admin_masters(message: Message):
    """Список мастеров"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    
    await show_masters_list(message)

@router.callback_query(F.data.startswith("admin_"))
async def admin_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка callback-ов из админ-панели"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    action = callback.data.replace("admin_", "")
    
    if action == "today":
        await show_today_appointments(callback.message)
    elif action == "week":
        await show_week_appointments(callback.message)
    elif action == "masters":
        await show_masters_list(callback.message)
    elif action == "stats":
        await show_statistics(callback.message)
    elif action == "back":
        await callback.message.edit_text(
            "👑 Административная панель\n\nВыберите действие:",
            reply_markup=get_admin_keyboard()
        )
    
    await callback.answer()

async def show_today_appointments(message):
    """Показать записи на сегодня"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        appointments = sheets_manager.get_appointments_by_date(today)
        
        if not appointments:
            await message.answer(
                f"📅 На сегодня ({today}) записей нет.",
                reply_markup=get_admin_actions_keyboard()
            )
            return
        
        text = f"📋 Записи на сегодня ({today}):\n\n"
        for apt in appointments:
            master = sheets_manager.get_master_by_id(apt['master_id'])
            master_name = master['name'] if master else 'Неизвестно'
            
            text += (
                f"⏰ {apt['time']}\n"
                f"👤 {apt['client_name']}\n"
                f"📞 {apt['client_phone']}\n"
                f"💇 {apt['service']}\n"
                f"👩 {master_name}\n"
                f"---\n"
            )
        
        await message.answer(
            text,
            reply_markup=get_admin_actions_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при получении записей на сегодня: {e}")
        await message.answer(
            "❌ Ошибка при получении записей.",
            reply_markup=get_admin_actions_keyboard()
        )

async def show_week_appointments(message):
    """Показать записи на неделю"""
    try:
        today = datetime.now()
        appointments_by_day = {}
        
        for i in range(7):
            date = (today + timedelta(days=i)).strftime('%Y-%m-%d')
            appointments = sheets_manager.get_appointments_by_date(date)
            if appointments:
                appointments_by_day[date] = appointments
        
        if not appointments_by_day:
            await message.answer(
                "📅 На ближайшую неделю записей нет.",
                reply_markup=get_admin_actions_keyboard()
            )
            return
        
        text = "📋 Записи на неделю:\n\n"
        for date, appointments in appointments_by_day.items():
            text += f"📅 {date}:\n"
            for apt in appointments:
                text += f"  ⏰ {apt['time']} - {apt['client_name']} ({apt['service']})\n"
            text += "\n"
        
        await message.answer(
            text,
            reply_markup=get_admin_actions_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при получении записей на неделю: {e}")
        await message.answer(
            "❌ Ошибка при получении записей.",
            reply_markup=get_admin_actions_keyboard()
        )

async def show_masters_list(message):
    """Показать список мастеров"""
    try:
        masters = sheets_manager.get_masters()
        
        if not masters:
            await message.answer(
                "📋 Список мастеров пуст.",
                reply_markup=get_admin_actions_keyboard()
            )
            return
        
        text = "👩 Список мастеров:\n\n"
        for master in masters:
            appointments = sheets_manager.get_master_appointments(master['id'])
            
            text += (
                f"🆔 ID: {master['id']}\n"
                f"👤 Имя: {master['name']}\n"
                f"💇 Специализация: {master['specialization']}\n"
                f"⏰ Опыт: {master['experience']}\n"
                f"📊 Записей: {len(appointments)}\n"
                f"---\n"
            )
        
        await message.answer(
            text,
            reply_markup=get_admin_actions_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка мастеров: {e}")
        await message.answer(
            "❌ Ошибка при получении списка мастеров.",
            reply_markup=get_admin_actions_keyboard()
        )

async def show_statistics(message):
    """Показать статистику"""
    try:
        all_appointments = sheets_manager.get_all_appointments()
        
        if not all_appointments:
            await message.answer(
                "📊 Статистика: записей пока нет.",
                reply_markup=get_admin_actions_keyboard()
            )
            return
        
        total = len(all_appointments)
        
        services = {}
        for apt in all_appointments:
            service = apt['service']
            services[service] = services.get(service, 0) + 1
        
        masters_count = {}
        for apt in all_appointments:
            master_id = apt['master_id']
            masters_count[master_id] = masters_count.get(master_id, 0) + 1
        
        confirmed = sum(1 for apt in all_appointments if apt.get('status') == 'confirmed')
        cancelled = sum(1 for apt in all_appointments if apt.get('status') == 'cancelled')
        
        text = (
            f"📊 Статистика записей:\n\n"
            f"📝 Всего записей: {total}\n"
            f"✅ Подтверждено: {confirmed}\n"
            f"❌ Отменено: {cancelled}\n\n"
            f"📈 По услугам:\n"
        )
        
        for service, count in services.items():
            text += f"  • {service}: {count}\n"
        
        text += f"\n👩 По мастерам:\n"
        for master_id, count in masters_count.items():
            master = sheets_manager.get_master_by_id(master_id)
            master_name = master['name'] if master else f"ID {master_id}"
            text += f"  • {master_name}: {count}\n"
        
        await message.answer(
            text,
            reply_markup=get_admin_actions_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await message.answer(
            "❌ Ошибка при получении статистики.",
            reply_markup=get_admin_actions_keyboard()
        )
