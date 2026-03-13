# handlers/errors.py
"""
Обработчики ошибок
"""
import logging
import traceback

from max_adapter import Router

logger = logging.getLogger(__name__)

router = Router(name="errors")

# Декоратор для обработки ошибок
def errors_handler():
    """Декоратор для обработки ошибок"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Ошибка в {func.__name__}: {e}")
                logger.error(traceback.format_exc())
                
                # Пытаемся отправить сообщение об ошибке пользователю
                try:
                    if args and hasattr(args[0], 'message'):
                        message = args[0].message
                        await message.answer(
                            "❌ Произошла внутренняя ошибка. Пожалуйста, попробуйте позже."
                        )
                    elif args and hasattr(args[0], 'callback_query'):
                        callback = args[0].callback_query
                        await callback.message.answer(
                            "❌ Произошла внутренняя ошибка. Пожалуйста, попробуйте позже."
                        )
                except:
                    pass
                
                return None
        return wrapper
    return decorator

# Глобальный обработчик ошибок
@router.errors()
async def global_error_handler(update, error):
    """Глобальный обработчик ошибок"""
    logger.error(f"❌ Глобальная ошибка при обработке обновления {update}: {error}")
    logger.error(traceback.format_exc())
    return True