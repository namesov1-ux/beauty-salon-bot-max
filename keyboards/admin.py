# keyboards/admin.py
"""
Админские клавиатуры
"""
from max_adapter import InlineKeyboardBuilder

def get_admin_keyboard():
    """Админская клавиатура"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Записи на сегодня", callback_data="admin_today")
    builder.button(text="📆 Записи на неделю", callback_data="admin_week")
    builder.button(text="👩 Список мастеров", callback_data="admin_masters")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.adjust(1)
    
    return builder.as_markup()

def get_admin_actions_keyboard():
    """Клавиатура действий админа"""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад в админку", callback_data="admin_back")
    builder.button(text="🏠 Главное меню", callback_data="back")
    builder.adjust(1)
    
    return builder.as_markup()
