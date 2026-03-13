# max_bot.py
"""
Точка входа для MAH платформы
"""
import os
import sys
import logging
import asyncio
import threading
from datetime import datetime
from flask import Flask, request, jsonify

from max_adapter import Bot, Dispatcher, MemoryStorage
from config import config
from handlers import start, booking, admin, errors
from utils.scheduler import setup_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Глобальные переменные
bot = None
dp = None
scheduler = None
app = Flask(__name__)

# Файл для блокировки
LOCK_FILE = "bot.lock"

def check_single_instance():
    """Проверка единственного экземпляра"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            if sys.platform == "win32":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(1, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    return False
            else:
                os.kill(pid, 0)
                return False
        except:
            os.remove(LOCK_FILE)
    
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return True

def cleanup_lock():
    """Удаляет lock-файл"""
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
        except:
            pass

def init_bot():
    """Инициализация бота для MAH"""
    global bot, dp
    
    logger.info("📝 Инициализация бота для MAH...")
    
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутеров
    dp.include_router(errors.router)
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(admin.router)
    
    logger.info("✅ Бот инициализирован для MAH")
    return bot, dp

def start_scheduler():
    """Запуск планировщика в отдельном потоке"""
    global scheduler, bot
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        scheduler = setup_scheduler(bot)
        scheduler.start()
        logger.info("✅ Планировщик запущен")
        
        loop.run_forever()
    except Exception as e:
        logger.error(f"❌ Ошибка в планировщике: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка входящих вебхуков от MAH"""
    global bot, dp
    
    try:
        data = request.json
        logger.info(f"📡 Получен webhook")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(dp.process_update(data))
        
        if result:
            logger.info("✅ Webhook обработан успешно")
        else:
            logger.warning("⚠️ Webhook обработан, но хендлер не найден")
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья"""
    return jsonify({
        "status": "healthy",
        "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "bot": "BeautySalon_sale_bot"
    })

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Грациозное завершение"""
    logger.info("🛑 Получен сигнал завершения")
    
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("✅ Планировщик остановлен")
    
    if bot:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.close())
        logger.info("✅ Сессия бота закрыта")
    
    cleanup_lock()
    
    return jsonify({"status": "shutdown completed"})

if __name__ == "__main__":
    if not check_single_instance():
        logger.error("❌ Бот уже запущен")
        sys.exit(1)
    
    try:
        init_bot()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        me = loop.run_until_complete(bot.get_me())
        logger.info(f"✅ Бот авторизован: @{me.get('username')} (ID: {me.get('id')})")
        
        scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
        scheduler_thread.start()
        
        if config.ADMIN_IDS:
            for admin_id in config.ADMIN_IDS:
                try:
                    loop.run_until_complete(bot.send_message(
                        admin_id,
                        f"✅ MAH бот запущен\n⏰ {datetime.now().strftime('%H:%M %d.%m')}"
                    ))
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")
        
        port = int(os.environ.get('PORT', 5000))
        
        logger.info("=" * 60)
        logger.info(f"🚀 MAH бот запускается на порту {port}")
        logger.info(f"📅 Время запуска: {datetime.now()}")
        logger.info(f"📊 PID процесса: {os.getpid()}")
        logger.info("=" * 60)
        
        app.run(host='0.0.0.0', port=port)
        
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        cleanup_lock()