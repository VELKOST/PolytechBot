# handlers/main_handlers.py
"""
Модуль с основными обработчиками команд, такими как /start.
"""

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot
from ru import WELCOME_TEXT
from handlers.statistics import send_statistics_options
from handlers.registration import start_registration

def send_welcome(message):
    """
    Отправляет приветственное сообщение с основным меню.
    """
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Моя статистика", callback_data="my_statistics"),
        InlineKeyboardButton("Известные мероприятия", callback_data="upcoming_events")
    )
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=markup)

@bot.message_handler(commands=['start'])
def handle_start(message):
    """
    Обработчик команды /start.
    """
    send_welcome(message)
