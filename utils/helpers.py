# utils/helpers.py
"""
Вспомогательные функции
"""
import re
from datetime import datetime, timedelta

def validate_phone(phone: str) -> bool:
    """
    Проверка формата телефона
    Допустимые форматы: +7XXXXXXXXXX, 8XXXXXXXXXX, XXXXXXXXXX
    """
    # Удаляем все нецифровые символы
    cleaned = re.sub(r'\D', '', phone)
    
    # Проверяем длину и начало
    if len(cleaned) == 11 and (cleaned.startswith('7') or cleaned.startswith('8')):
        return True
    elif len(cleaned) == 10:
        return True
    return False

def format_phone(phone: str) -> str:
    """
    Форматирование номера телефона в единый формат +7XXXXXXXXXX
    """
    cleaned = re.sub(r'\D', '', phone)
    
    if len(cleaned) == 11 and cleaned.startswith('8'):
        cleaned = '7' + cleaned[1:]
    elif len(cleaned) == 10:
        cleaned = '7' + cleaned
    
    return '+' + cleaned

def format_datetime(dt: datetime) -> str:
    """Форматирование даты для отображения"""
    return dt.strftime('%d.%m.%Y %H:%M')

def get_weekday_name(weekday: int) -> str:
    """Получение названия дня недели"""
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    return days[weekday]

def parse_time(time_str: str) -> datetime:
    """Парсинг строки времени"""
    return datetime.strptime(time_str, '%H:%M')

def generate_time_slots(start_hour: int = 10, end_hour: int = 21, 
                       duration: int = 30) -> list:
    """Генерация временных слотов"""
    slots = []
    current = datetime.now().replace(hour=start_hour, minute=0, second=0)
    end = datetime.now().replace(hour=end_hour, minute=0, second=0)
    
    while current < end:
        slots.append(current.strftime('%H:%M'))
        current += timedelta(minutes=duration)
    
    return slots

def is_working_day(date: datetime) -> bool:
    """Проверка, является ли день рабочим"""
    # Суббота (5) и Воскресенье (6) - выходные
    return date.weekday() < 5
