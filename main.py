import telebot
import json
import uuid
import random
import schedule
import time
from admin import setup_admin_handlers
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from ru import WELCOME_TEXT

TOKEN = ''
bot = telebot.TeleBot(TOKEN)

RAND_MESSAGES = [
    "Привет, {name}! Участвовал(а) в мероприятии на этой неделе? Поделись своими впечатлениями! 😊",
    "Напоминаем, что скоро пройдет важное событие! Не забудь зарегистрироваться, {name}! 🚀",
    "Эй, {name}! Как продвигается твой учебный проект? Дай знать, если нужна помощь! 🧑‍🏫"
]

def send_random_messages():
    for student in data_store['students']:
        telegram_id = student['telegram_id']
        first_name = student['first_name']
        random_message = random.choice(RAND_MESSAGES).format(name=first_name)
        bot.send_message(telegram_id, random_message)

# Schedule message sending every 20 seconds
schedule.every(20).seconds.do(send_random_messages)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)  # Check every second for due jobs

# Start the schedule in the background
import threading
threading.Thread(target=run_schedule).start()

def load_data(filename='basa.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for key in ['students', 'activities', 'achievements', 'admins']:
                if key not in data:
                    data[key] = []
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {'students': [], 'activities': [], 'achievements': [], 'admins': []}


def save_data(data):
    with open('basa.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

data_store = load_data()

def is_user_registered(telegram_id):
    return any(student['telegram_id'] == telegram_id for student in data_store['students'])

def add_student(telegram_id, first_name, last_name, group_number):
    new_student = {
        'telegram_id': telegram_id,
        'first_name': first_name,
        'last_name': last_name,
        'group_number': group_number
    }
    data_store['students'].append(new_student)
    save_data(data_store)

setup_admin_handlers(bot)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Моя статистика", callback_data="my_statistics"),
        InlineKeyboardButton("Известные мероприятия", callback_data="upcoming_events")
    )
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "my_statistics")
def handle_my_statistics(call):
    bot.answer_callback_query(call.id)
    telegram_id = call.from_user.id

    if not is_user_registered(telegram_id):
        bot.send_message(call.message.chat.id, "Зарегистрируйтесь, чтобы продолжить.")
        start_registration(call.message)
    else:
        send_statistics_options(call.message)


def start_registration(message):
    msg = bot.send_message(message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(msg, get_last_name)

def get_last_name(message):
    first_name = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введите вашу фамилию:")
    bot.register_next_step_handler(msg, get_group_number, first_name)

def get_group_number(message, first_name):
    last_name = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введите номер группы:")
    bot.register_next_step_handler(msg, complete_registration, first_name, last_name)

def complete_registration(message, first_name, last_name):
    group_number = message.text.strip()
    telegram_id = message.from_user.id
    add_student(telegram_id, first_name, last_name, group_number)
    bot.send_message(message.chat.id, "Вы успешно зарегистрированы!")
    send_welcome(message)

def send_statistics_options(message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Похвастаться", callback_data="show_achievements"),
        InlineKeyboardButton("Мои мероприятия", callback_data="my_events"),
        InlineKeyboardButton("Информация обо мне", callback_data="my_info"),
        InlineKeyboardButton("Изменить информацию о себе", callback_data="edit_info"),
        InlineKeyboardButton("Назад", callback_data="back_to_options")
    )
    bot.send_message(message.chat.id, "Что делаем в этот раз?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "my_info")
def handle_my_info(call):
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    telegram_id = call.from_user.id

    user = next((s for s in data_store['students'] if s['telegram_id'] == telegram_id), None)
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
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    msg = bot.send_message(call.message.chat.id, "Введите ваше новое имя:")
    bot.register_next_step_handler(msg, edit_last_name)


def edit_last_name(message):
    first_name = message.text.strip()
    if not first_name:
        msg = bot.send_message(message.chat.id, "Имя не может быть пустым. Пожалуйста, введите ваше имя:")
        bot.register_next_step_handler(msg, edit_last_name)
        return

    msg = bot.send_message(message.chat.id, "Введите вашу новую фамилию:")
    bot.register_next_step_handler(msg, edit_group_number, first_name)


def edit_group_number(message, first_name):
    last_name = message.text.strip()
    if not last_name:
        msg = bot.send_message(message.chat.id, "Фамилия не может быть пустой. Пожалуйста, введите вашу фамилию:")
        bot.register_next_step_handler(msg, edit_group_number, first_name)
        return

    msg = bot.send_message(message.chat.id, "Введите ваш новый номер группы:")
    bot.register_next_step_handler(msg, update_user_info, first_name, last_name)


def update_user_info(message, first_name, last_name):
    group_number = message.text.strip()
    if not group_number:
        msg = bot.send_message(message.chat.id, "Номер группы не может быть пустым. Пожалуйста, введите номер группы:")
        bot.register_next_step_handler(msg, update_user_info, first_name, last_name)
        return

    telegram_id = message.from_user.id

    for student in data_store['students']:
        if student['telegram_id'] == telegram_id:
            student.update({
                'first_name': first_name,
                'last_name': last_name,
                'group_number': group_number
            })
            break

    save_data(data_store)
    bot.send_message(message.chat.id, "Ваша информация успешно обновлена!")
    send_statistics_options(message)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_statistics")
def handle_back_to_statistics(call):
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_statistics_options(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "show_achievements")
def show_achievements(call):
    bot.answer_callback_query(call.id)
    telegram_id = call.from_user.id

    student = next((s for s in data_store['students'] if s['telegram_id'] == telegram_id), None)
    if student:
        achievements = data_store['achievements']
        past_events = [
            a for a in data_store['activities'] if a['confirmed']
        ]
        
        if past_events:
            text = "Выберите мероприятие, в котором вы участвовали:\n\n"
            markup = InlineKeyboardMarkup(row_width=1)
            for event in past_events:
                markup.add(InlineKeyboardButton(event['title'], callback_data=f"select_event_{event['id']}"))
            bot.send_message(call.message.chat.id, text, reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "Нет мероприятий для выбора.")

    else:
        bot.send_message(call.message.chat.id, "Пожалуйста, сначала зарегистрируйтесь.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_event_"))
def select_event(call):
    event_id = call.data.split("_")[-1]
    msg = bot.send_message(call.message.chat.id, "Введите место, которое вы заняли (1-е, 2-е, 3-е место и т.д.):")
    bot.register_next_step_handler(msg, get_achievement_result, event_id)

def get_achievement_result(message, event_id):
    place = message.text.strip()
    if not place:
        msg = bot.send_message(message.chat.id, "Место не может быть пустым. Пожалуйста, введите место:")
        bot.register_next_step_handler(msg, get_achievement_result, event_id)
        return

    telegram_id = message.from_user.id
    achievement = {
        'student_id': telegram_id,
        'event_id': event_id,
        'place': place,
        'date': datetime.now().isoformat(),
        'confirmed': False
    }

    data_store.setdefault('achievements', []).append(achievement)
    save_data(data_store)
    
    bot.send_message(message.chat.id, "Ваше достижение успешно передано администрации!")
    send_statistics_options(message)

@bot.callback_query_handler(func=lambda call: call.data == "my_events")
def show_my_events(call):
    bot.answer_callback_query(call.id)
    telegram_id = call.from_user.id

    student = next((s for s in data_store['students'] if s['telegram_id'] == telegram_id), None)
    if student:
        student_id = student.get('telegram_id')

        events = [
            ach for ach in data_store['achievements']
            if ach['student_id'] == student_id
        ]

        if events:
            events_text = "Ваши мероприятия:\n\n"
            for achievement in events:
                event = next((a for a in data_store['activities'] if a['id'] == achievement['event_id']), None)
                if event:
                    events_text += (
                        f"Название: {event['title']}\n"
                        f"Описание: {event['description']}\n"
                        f"Дата: {event['date']}\n\n"
                    )
                else:
                    events_text += "Мероприятие не найдено.\n\n"
        else:
            events_text = "У вас пока нет зарегистрированных мероприятий."

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("Назад", callback_data="back_to_statistics"))
        
        bot.send_message(call.message.chat.id, events_text, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Пожалуйста, сначала зарегистрируйтесь.")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_options")
def handle_back_to_options(call):
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_welcome(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "upcoming_events")
def handle_upcoming_events(call):
    bot.answer_callback_query(call.id)

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Узнать о предстоящих мероприятиях", callback_data="get_events"),
        InlineKeyboardButton("Сообщить о мероприятии", callback_data="report_event"),
        InlineKeyboardButton("Назад", callback_data="back_to_welcome")
    )
    
    bot.send_message(call.message.chat.id, "Так, куда дальше? Выбирай ниже 👇", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "get_events")
def get_events(call):
    data_store = load_data()
    
    activities = data_store.get('activities', [])
    current_date = datetime.now()

    upcoming_events = []
    for event in activities:
        event_date = datetime.strptime(event['date'], '%Y-%m-%d')

        if event.get('confirmed', False) and event_date >= current_date:
            upcoming_events.append(event)

    if not upcoming_events:
        events_text = "На данный момент предстоящих мероприятий нет."
    else:
        events_text = "Предстоящие мероприятия:\n\n"
        for event in upcoming_events:
            events_text += (
                f"Название: {event['title']}\n"
                f"Описание: {event['description']}\n"
                f"Дата: {event['date']}\n"
                f"Место: {event['location']}\n\n"
            )

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("Назад", callback_data="back_to_upcoming_events"))
    bot.send_message(call.message.chat.id, events_text.strip(), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "report_event")
def report_event(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "Введите название мероприятия:")
    bot.register_next_step_handler(msg, get_activity_description_title)

def get_activity_description_title(message):
    activity_title = message.text.strip()
    if not activity_title:
        msg = bot.send_message(message.chat.id, "Название мероприятия не может быть пустым. Пожалуйста, введите название:")
        bot.register_next_step_handler(msg, get_activity_description_title)
        return
    msg = bot.send_message(message.chat.id, "Введите описание мероприятия:")
    bot.register_next_step_handler(msg, get_activity_description, activity_title)

def get_activity_description(message, activity_title):
    activity_description = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введите дату проведения мероприятия (ГГГГ-ММ-ДД):")
    bot.register_next_step_handler(msg, get_activity_date, activity_title, activity_description)

def get_activity_date(message, activity_title, activity_description):
    activity_date = message.text.strip()
    try:
        datetime.strptime(activity_date, '%Y-%m-%d') 
    except ValueError:
        msg = bot.send_message(message.chat.id, "Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД:")
        bot.register_next_step_handler(msg, get_activity_date, activity_title, activity_description)
        return
    msg = bot.send_message(message.chat.id, "Введите место проведения мероприятия:")
    bot.register_next_step_handler(msg, get_activity_location, activity_title, activity_description, activity_date)

def get_activity_location(message, activity_title, activity_description, activity_date):
    activity_location = message.text.strip()
    if not activity_location:
        msg = bot.send_message(message.chat.id, "Место проведения не может быть пустым. Пожалуйста, введите место:")
        bot.register_next_step_handler(msg, get_activity_location, activity_title, activity_description, activity_date)
        return

    new_activity = {
        'id': str(uuid.uuid4()),  
        'title': activity_title,
        'description': activity_description,
        'date': activity_date,
        'location': activity_location,
        'confirmed': False,
        'submitter_id': message.from_user.id
    }

    data_store.setdefault('activities', []).append(new_activity)
    save_data(data_store)

    bot.send_message(message.chat.id, "Информация о мероприятии успешно сохранена и ожидает подтверждения.")


@bot.callback_query_handler(func=lambda call: call.data == "back_to_upcoming_events")
def back_to_upcoming_events(call):
    handle_upcoming_events(call)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_welcome")
def handle_back_to_welcome(call):
    send_welcome(call.message)

if __name__ == '__main__':
    bot.polling(none_stop=True)
