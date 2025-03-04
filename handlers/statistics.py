# handlers/statistics.py
"""
Модуль с обработчиками для работы со статистикой и информацией пользователя.
"""

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot
from data_manager import load_data, save_data


def send_statistics_options(message):
    """
    Отправляет меню статистики пользователю.
    """
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Похвастаться", callback_data="show_achievements"),
        InlineKeyboardButton("Мои мероприятия", callback_data="my_events"),
        InlineKeyboardButton("Информация обо мне", callback_data="my_info"),
        InlineKeyboardButton("Изменить информацию о себе", callback_data="edit_info"),
        InlineKeyboardButton("Назад", callback_data="back_to_options")
    )
    bot.send_message(message.chat.id, "Что делаем в этот раз?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "my_statistics")
def handle_my_statistics(call):
    """
    Обрабатывает запрос статистики пользователя.
    """
    bot.answer_callback_query(call.id)
    telegram_id = call.from_user.id
    data = load_data()
    if not any(student['telegram_id'] == telegram_id for student in data.get('students', [])):
        bot.send_message(call.message.chat.id, "Зарегистрируйтесь, чтобы продолжить.")

        from handlers.registration import start_registration
        start_registration(call.message)
    else:
        send_statistics_options(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "my_info")
def handle_my_info(call):
    """
    Отправляет информацию о пользователе.
    """
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    telegram_id = call.from_user.id
    data = load_data()
    user = next((s for s in data.get('students', []) if s['telegram_id'] == telegram_id), None)
    if user:
        user_info_text = (
            f"Ваша информация:\n"
            f"Имя: {user['first_name']}\n"
            f"Фамилия: {user['last_name']}\n"
            f"Группа: {user['group_number']}"
        )
    else:
        user_info_text = "Информация о вас не найдена. Пожалуйста, зарегистрируйтесь."
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("Назад", callback_data="back_to_statistics"))
    bot.send_message(call.message.chat.id, user_info_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "edit_info")
def handle_edit_info(call):
    """
    Запускает процесс изменения информации пользователя.
    """
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    msg = bot.send_message(call.message.chat.id, "Введите ваше новое имя:")
    bot.register_next_step_handler(msg, edit_last_name)

def edit_last_name(message):
    """
    Получает новое имя пользователя.
    """
    first_name = message.text.strip()
    if not first_name:
        msg = bot.send_message(message.chat.id, "Имя не может быть пустым. Пожалуйста, введите ваше имя:")
        bot.register_next_step_handler(msg, edit_last_name)
        return
    msg = bot.send_message(message.chat.id, "Введите вашу новую фамилию:")
    bot.register_next_step_handler(msg, edit_group_number, first_name)

def edit_group_number(message, first_name):
    """
    Получает новую фамилию пользователя.
    """
    last_name = message.text.strip()
    if not last_name:
        msg = bot.send_message(message.chat.id, "Фамилия не может быть пустой. Пожалуйста, введите вашу фамилию:")
        bot.register_next_step_handler(msg, edit_group_number, first_name)
        return
    msg = bot.send_message(message.chat.id, "Введите ваш новый номер группы:")
    bot.register_next_step_handler(msg, update_user_info, first_name, last_name)

def update_user_info(message, first_name, last_name):
    """
    Обновляет информацию о пользователе.
    """
    group_number = message.text.strip()
    if not group_number:
        msg = bot.send_message(message.chat.id, "Номер группы не может быть пустым. Пожалуйста, введите номер группы:")
        bot.register_next_step_handler(msg, update_user_info, first_name, last_name)
        return
    telegram_id = message.from_user.id
    data = load_data()
    for student in data.get('students', []):
        if student['telegram_id'] == telegram_id:
            student.update({
                'first_name': first_name,
                'last_name': last_name,
                'group_number': group_number
            })
            break
    save_data(data)
    bot.send_message(message.chat.id, "Ваша информация успешно обновлена!")
    send_statistics_options(message)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_statistics")
def handle_back_to_statistics(call):
    """
    Обрабатывает кнопку "Назад" в меню статистики.
    """
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_statistics_options(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_options")
def handle_back_to_options(call):
    """
    Возвращает пользователя к главному меню.
    """
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    from handlers.main_handlers import send_welcome
    send_welcome(call.message)
