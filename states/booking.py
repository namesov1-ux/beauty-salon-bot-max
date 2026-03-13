# states/booking.py
"""
Состояния для FSM процесса записи
"""
from mah_adapter import State, StateGroup

class BookingStates(StateGroup):
    """Состояния для процесса записи"""
    choosing_service = State()      # Выбор услуги
    choosing_master = State()       # Выбор мастера
    choosing_date = State()         # Выбор даты
    choosing_time = State()         # Выбор времени
    entering_name = State()         # Ввод имени
    entering_phone = State()        # Ввод телефона
    confirming = State()            # Подтверждение