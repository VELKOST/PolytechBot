# bot_instance.py
"""
Модуль для инициализации экземпляра телеграм-бота.
Загружает конфигурацию и настраивает обработчики для администраторов.
"""

import telebot
from config import TOKEN
from admin import setup_admin_handlers

# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

# Настраиваем админские обработчики
setup_admin_handlers(bot)
