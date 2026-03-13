# max_adapter.py
"""
Адаптер для MAH API - ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
import logging
import sys
from typing import Dict, Any, Optional

# Настраиваем логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ============ Базовые классы ============
class User:
    def __init__(self, id: int, first_name: str = "", last_name: str = None, username: str = None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

class Chat:
    def __init__(self, id: int, type: str = "private"):
        self.id = id
        self.type = type

class Message:
    def __init__(self, message_id: int, from_user: User, chat: Chat, date: int, text: str = None, bot=None):
        self.message_id = message_id
        self.from_user = from_user
        self.chat = chat
        self.date = date
        self.text = text
        self.bot = bot
        self.chat_id = chat.id
    
    @property
    def from_(self):
        return self.from_user

class CallbackQuery:
    def __init__(self, id: str, from_user: User, message: Message, data: str):
        self.id = id
        self.from_user = from_user
        self.message = message
        self.data = data
    
    @property
    def from_(self):
        return self.from_user

# ============ FSM классы ============
class State:
    def __init__(self, state=None):
        self.state = state
    
    def __str__(self):
        return str(self.state) if self.state is not None else ""

class StateGroup:
    pass

class FSMContext:
    def __init__(self, storage, key: str):
        self.storage = storage
        self.key = key
    
    async def set_state(self, state):
        if state is None:
            state_str = None
        elif hasattr(state, 'state'):
            state_str = state.state
        else:
            state_str = str(state)
        await self.storage.set_state(self.key, state_str)
    
    async def get_state(self):
        return await self.storage.get_state(self.key)
    
    async def set_data(self, data: Dict[str, Any]):
        await self.storage.set_data(self.key, data)
    
    async def get_data(self) -> Dict[str, Any]:
        return await self.storage.get_data(self.key)
    
    async def update_data(self, **kwargs):
        data = await self.get_data()
        data.update(kwargs)
        await self.set_data(data)
    
    async def clear(self):
        await self.storage.set_state(self.key, None)
        await self.storage.set_data(self.key, {})

class MemoryStorage:
    def __init__(self):
        self._data = {}
    
    async def set_state(self, key: str, state: Optional[str]):
        if key not in self._data:
            self._data[key] = {'state': None, 'data': {}}
        self._data[key]['state'] = state
    
    async def get_state(self, key: str):
        return self._data.get(key, {}).get('state')
    
    async def set_data(self, key: str, data: Dict[str, Any]):
        if key not in self._data:
            self._data[key] = {'state': None, 'data': {}}
        self._data[key]['data'] = data.copy()
    
    async def get_data(self, key: str) -> Dict[str, Any]:
        return self._data.get(key, {}).get('data', {}).copy()

# ============ Фильтры ============
class Command:
    def __init__(self, *commands: str):
        self.commands = commands
    
    def __call__(self, message: Message) -> bool:
        if not message or not message.text:
            return False
        return any(message.text.startswith(f'/{cmd}') for cmd in self.commands)

class F:
    class data:
        def __init__(self, value=None):
            self.value = value
            self._check_startswith = False
        
        def __call__(self, callback: CallbackQuery) -> bool:
            if self._check_startswith:
                return callback.data.startswith(self.value)
            if self.value is not None:
                return callback.data == self.value
            return True
        
        @classmethod
        def startswith(cls, prefix: str):
            """Классовый метод для создания фильтра startswith"""
            filter_obj = cls(prefix)
            filter_obj._check_startswith = True
            return filter_obj

# ============ Роутер ============
class Handler:
    def __init__(self, callback, filters):
        self.callback = callback
        self.filters = filters

class Router:
    def __init__(self, name: str = None):
        self.name = name
        self.message_handlers = []
        self.callback_handlers = []
    
    def message(self, *filters):
        def decorator(func):
            self.message_handlers.append(Handler(func, filters))
            return func
        return decorator
    
    def callback_query(self, *filters):
        def decorator(func):
            self.callback_handlers.append(Handler(func, filters))
            return func
        return decorator
    
    def errors(self):
        def decorator(func):
            return func
        return decorator

# ============ Клавиатуры ============
class KeyboardButton:
    def __init__(self, text: str, request_contact: bool = False):
        self.text = text
        self.request_contact = request_contact

class ReplyKeyboardMarkup:
    def __init__(self, keyboard, resize_keyboard=False, one_time_keyboard=False):
        self.keyboard = keyboard
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard

class InlineKeyboardButton:
    def __init__(self, text: str, callback_data: str = None, url: str = None):
        self.text = text
        self.callback_data = callback_data
        self.url = url

class InlineKeyboardMarkup:
    def __init__(self, inline_keyboard):
        self.inline_keyboard = inline_keyboard

class InlineKeyboardBuilder:
    def __init__(self):
        self.buttons = []
    
    def button(self, text: str, callback_data: str = None, url: str = None):
        self.buttons.append(InlineKeyboardButton(text, callback_data, url))
        return self
    
    def adjust(self, *args):
        return self
    
    def as_markup(self):
        keyboard = []
        row = []
        for btn in self.buttons:
            row.append(btn)
            if len(row) >= 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)

# ============ Бот ============
class Bot:
    def __init__(self, token: str, base_url: str = None, default=None):
        self.token = token
        self._me = None
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = None, reply_markup=None) -> Dict:
        logger.info(f"📤 Отправка сообщения для {chat_id}")
        return {"ok": True, "result": {"message_id": 123}}
    
    async def edit_message_text(self, text: str, chat_id: int = None, message_id: int = None, **kwargs) -> Dict:
        logger.info(f"✏️ Редактирование сообщения")
        return {"ok": True}
    
    async def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> Dict:
        logger.info(f"🔄 Ответ на callback")
        return {"ok": True}
    
    async def delete_webhook(self, drop_pending_updates: bool = False):
        logger.info("🔄 Webhook удален")
        return True
    
    async def get_me(self) -> Dict:
        if not self._me:
            self._me = {"id": 8639995807, "username": "BeautySalon_sale_bot"}
        return self._me
    
    async def close(self):
        logger.info("🔌 Сессия бота закрыта")

# ============ Диспетчер ============
class Dispatcher:
    def __init__(self, storage=None):
        self.storage = storage or MemoryStorage()
        self.message_handlers = []
        self.callback_handlers = []
    
    def include_router(self, router: Router):
        self.message_handlers.extend(router.message_handlers)
        self.callback_handlers.extend(router.callback_handlers)
        logger.info(f"📦 Подключен роутер: {router.name}")
    
    async def process_update(self, update_data: Dict) -> bool:
        try:
            if 'message' in update_data:
                return await self._process_message(update_data['message'])
            elif 'callback_query' in update_data:
                return await self._process_callback(update_data['callback_query'])
        except Exception as e:
            logger.error(f"❌ Ошибка обработки update: {e}")
        return False
    
    async def _process_message(self, data: Dict) -> bool:
        user = User(
            id=data['from']['id'],
            first_name=data['from'].get('first_name', ''),
            last_name=data['from'].get('last_name'),
            username=data['from'].get('username')
        )
        chat = Chat(id=data['chat']['id'])
        message = Message(
            message_id=data['message_id'],
            from_user=user,
            chat=chat,
            date=data['date'],
            text=data.get('text'),
            bot=self
        )
        
        for handler in self.message_handlers:
            ok = True
            for f in handler.filters:
                if callable(f) and not f(message):
                    ok = False
                    break
            if ok:
                state = FSMContext(self.storage, f"{chat.id}:{user.id}")
                await handler.callback(message, state)
                return True
        return False
    
    async def _process_callback(self, data: Dict) -> bool:
        user = User(
            id=data['from']['id'],
            first_name=data['from'].get('first_name', ''),
            last_name=data['from'].get('last_name'),
            username=data['from'].get('username')
        )
        chat = Chat(id=data['message']['chat']['id'])
        message = Message(
            message_id=data['message']['message_id'],
            from_user=user,
            chat=chat,
            date=data['message']['date'],
            text=data['message'].get('text'),
            bot=self
        )
        callback = CallbackQuery(
            id=data['id'],
            from_user=user,
            message=message,
            data=data['data']
        )
        
        for handler in self.callback_handlers:
            ok = True
            for f in handler.filters:
                if callable(f):
                    result = f(callback)
                    if not result:
                        ok = False
                        break
            if ok:
                state = FSMContext(self.storage, f"{chat.id}:{user.id}")
                await handler.callback(callback, state)
                return True
        return False
    
    async def start_polling(self, bot, **kwargs):
        logger.info("ℹ️ Polling не используется")
        pass