# utils/scheduler.py
"""
Планировщик задач для напоминаний
"""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from max_adapter import Bot
from database.google_sheets import sheets_manager
from config import config

logger = logging.getLogger(__name__)

def setup_scheduler(bot: Bot):
    """
    Настройка планировщика для отправки напоминаний
    """
    scheduler = AsyncIOScheduler()
    
    async def check_and_schedule_reminders():
        """Проверка записей и планирование напоминаний"""
        try:
            # Получаем текущую дату
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')
            tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
            
            logger.info(f"Планировщик: проверка записей на {tomorrow}")
            
            # Получаем записи на завтра
            appointments = sheets_manager.get_appointments_by_date(tomorrow)
            
            if not appointments:
                logger.info("Планировщик: записей на завтра нет")
                return
            
            logger.info(f"Планировщик: найдено {len(appointments)} записей на завтра")
            
            for appointment in appointments:
                # Проверяем статус записи
                if appointment.get('status') != 'confirmed':
                    continue
                
                # Проверяем, не отправляли ли уже напоминание
                if not is_reminder_sent(appointment):
                    await send_reminder(bot, appointment)
                    mark_reminder_sent(appointment)
                        
        except Exception as e:
            logger.error(f"Ошибка при проверке напоминаний: {e}")
    
    def is_reminder_sent(appointment):
        """
        Проверка, отправлено ли уже напоминание
        В реальном проекте здесь должна быть проверка по БД
        """
        # Сейчас просто возвращаем False, чтобы напоминания отправлялись
        # Позже можно добавить поле 'reminder_sent' в таблицу schedule
        return False
    
    def mark_reminder_sent(appointment):
        """
        Отметить, что напоминание отправлено
        В реальном проекте здесь должно быть обновление БД
        """
        # Заглушка
        logger.info(f"Напоминание отмечено как отправленное для записи {appointment['date']} {appointment['time']}")
    
    async def send_reminder(bot: Bot, appointment):
        """Отправка напоминания клиенту"""
        try:
            # Получаем информацию о мастере
            master = sheets_manager.get_master_by_id(appointment['master_id'])
            master_name = master['name'] if master else 'Неизвестно'
            
            reminder_text = (
                f"🔔 Напоминание о записи!\n\n"
                f"Вы записаны в салон {config.SALON_NAME}\n"
                f"📅 Дата: {appointment['date']}\n"
                f"⏰ Время: {appointment['time']}\n"
                f"💇 Услуга: {appointment['service']}\n"
                f"👩 Мастер: {master_name}\n\n"
                f"Ждем вас!"
            )
            
            logger.info(f"📨 Напоминание для записи {appointment['date']} {appointment['time']}")
            logger.debug(f"Текст напоминания: {reminder_text}")
            
            # Здесь нужно получить chat_id пользователя
            # В текущей версии user_id не сохраняется, поэтому это заглушка
            # В будущем можно добавить:
            # if 'user_id' in appointment:
            #     await bot.send_message(appointment['user_id'], reminder_text)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания: {e}")
    
    # Добавляем задачу для проверки каждый час
    scheduler.add_job(
        check_and_schedule_reminders,
        'interval',
        hours=1,
        id='reminder_check',
        replace_existing=True
    )
    
    # Добавляем задачу для немедленного запуска через 5 секунд после старта
    scheduler.add_job(
        check_and_schedule_reminders,
        DateTrigger(run_date=datetime.now() + timedelta(seconds=5)),
        id='initial_reminder_check',
        replace_existing=True
    )
    
    logger.info("Планировщик напоминаний настроен")
    return scheduler