# keyboards/inline.py
"""
Инлайн клавиатуры (InlineKeyboardMarkup)
"""
from datetime import datetime, timedelta
from max_adapter import InlineKeyboardBuilder

def get_services_keyboard():
    """Клавиатура с услугами"""
    services = [
        "💅 Маникюр",
        "💆 Педикюр",
        "✂️ Стрижка",
        "🎨 Окрашивание",
        "💇 Укладка",
        "👰 Свадебная прическа"
    ]
    
    builder = InlineKeyboardBuilder()
    for service in services:
        builder.button(
            text=service,
            callback_data=f"service_{service}"
        )
    builder.adjust(2)
    
    return builder.as_markup()

def get_masters_keyboard(masters):
    """Клавиатура с мастерами"""
    builder = InlineKeyboardBuilder()
    for master in masters:
        text = f"{master['name']} ({master['specialization']})"
        builder.button(
            text=text,
            callback_data=f"master_{master['id']}"
        )
    builder.button(text="◀️ Назад", callback_data="back")
    builder.adjust(1)
    
    return builder.as_markup()

def get_calendar_keyboard():
    """Клавиатура с датами"""
    builder = InlineKeyboardBuilder()
    
    today = datetime.now()
    for i in range(7):
        date = today + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        display_str = date.strftime('%d.%m')
        
        if date.weekday() >= 5:
            display_str = f"🌟 {display_str}"
        
        builder.button(
            text=display_str,
            callback_data=f"date_{date_str}"
        )
    
    builder.button(text="◀️ Назад", callback_data="back")
    builder.adjust(3, 4)
    
    return builder.as_markup()

def get_time_slots_keyboard(slots):
    """Клавиатура с временными слотами"""
    builder = InlineKeyboardBuilder()
    
    for slot in slots:
        builder.button(
            text=slot,
            callback_data=f"time_{slot}"
        )
    
    builder.button(text="◀️ Назад", callback_data="back")
    builder.adjust(3)
    
    return builder.as_markup()

def get_confirmation_keyboard():
    """Клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(2)
    
    return builder.as_markup()

def get_back_keyboard():
    """Клавиатура с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="back")
    
    return builder.as_markup()
