# handlers/registration.py
"""
Модуль с обработчиками для регистрации новых пользователей.
"""

from bot_instance import bot

from data_manager import load_data, add_student

def start_registration(message):
    """
    Инициирует процесс регистрации пользователя.
    """
    msg = bot.send_message(message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(msg, get_last_name)

def get_last_name(message):
    """
    Получает имя пользователя и запрашивает фамилию.
    """
    first_name = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введите вашу фамилию:")
    bot.register_next_step_handler(msg, get_group_number, first_name)

def get_group_number(message, first_name):
    """
    Получает фамилию и запрашивает номер группы.
    """
    last_name = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введите номер группы:")
    bot.register_next_step_handler(msg, complete_registration, first_name, last_name)

def complete_registration(message, first_name, last_name):
    """
    Завершает регистрацию, сохраняя данные пользователя.
    """
    group_number = message.text.strip()
    telegram_id = message.from_user.id
    data = load_data()
    add_student(data, telegram_id, first_name, last_name, group_number)
    bot.send_message(message.chat.id, "Вы успешно зарегистрированы!")

    from handlers.statistics import send_statistics_options
    send_statistics_options(message)
