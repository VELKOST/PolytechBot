# main.py
"""
Точка входа в приложение.
Создает экземпляр бота и запускает его, а также планировщик задач.
"""

from bot_instance import bot
from schedule_manager import start_scheduler

# Импорт всех файлов с обработчиками
import handlers.main_handlers
import handlers.registration
import handlers.statistics
import handlers.events

if __name__ == '__main__':
    start_scheduler()  # Запуск планировщика случайных сообщений
    bot.polling(none_stop=True)
