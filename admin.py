import json
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

def load_data(filename='basa.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for key in ['students', 'activities', 'achievements', 'admins']:
                data.setdefault(key, [])
            return data
    except FileNotFoundError:
        return {'students': [], 'activities': [], 'achievements': [], 'admins': []}

def save_data(data, filename='basa.json'):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def setup_admin_handlers(bot: TeleBot):
    @bot.message_handler(commands=['admin'])
    def handle_admin_command(message):
        data = load_data()
        admins = {admin['telegram_id'] for admin in data.get('admins', [])}

        if message.from_user.id not in admins:
            bot.send_message(message.chat.id, "У вас нет прав администратора.")
            return

        send_admin_menu(message.chat.id)

    def send_admin_menu(chat_id):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Добавить администратора", callback_data="view_students:0"),
            InlineKeyboardButton("Подтвердить мероприятия", callback_data="approve_events"),
            InlineKeyboardButton("Подтвердить достижения студента", callback_data="approve_student_achievements"),
            InlineKeyboardButton("Редактировать мероприятия", callback_data="edit_events"),
            InlineKeyboardButton("Выгрузка по мероприятиям", callback_data="export_event_data"),
            InlineKeyboardButton("Выгрузка пользователей и их достижения", callback_data="export_users_and_achievements"),
        )
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_back"))
    def handle_admin_back(call):
        bot.answer_callback_query(call.id)
        send_admin_menu(call.message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == "export_event_data")
    def export_event_data(call):
        bot.answer_callback_query(call.id)
        data = load_data()
        events_text = "Отчет по мероприятиям с участниками:\n\n"

        for event in data['activities']:
            if event.get('confirmed', False):
                events_text += (
                    f"Название мероприятия: {event['title']}\n"
                    f"Дата: {event['date']}\n"
                    f"Место: {event['location']}\n"
                    "Участники и занятые места:\n"
                )
                
                participants = [
                    ach for ach in data['achievements']
                    if ach['event_id'] == event['id']
                ]
                
                if participants:
                    for achievement in participants:
                        student = next((s for s in data['students'] if s['telegram_id'] == achievement['student_id']), None)
                        if student:
                            events_text += (
                                f"Имя: {student['first_name']} {student['last_name']}\n"
                                f"Номер группы: {student['group_number']}\n"
                                f"Занятое место: {achievement['place']}\n\n"
                            )
                else:
                    events_text += "Нет зарегистрированных участников.\n\n"

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("Назад", callback_data="admin_back"))
        bot.send_message(call.message.chat.id, events_text.strip(), reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "export_users_and_achievements")
    def export_users_and_achievements(call):
        bot.answer_callback_query(call.id)
        data = load_data()
        users_text = "Отчет по пользователям и их достижениям:\n\n"

        for student in data['students']:
            users_text += (
                f"Имя: {student['first_name']} {student['last_name']}\n"
                f"Группа: {student['group_number']}\n"
            )
            achievements = [
                ach for ach in data['achievements']
                if ach['student_id'] == student['telegram_id']
            ]

            if achievements:
                users_text += "Достижения:\n"
                for achievement in achievements:
                    event = next((evt for evt in data['activities'] if evt['id'] == achievement['event_id']), None)
                    if event:
                        users_text += (
                            f" - Мероприятие: {event['title']}, место: {achievement['place']}\n"
                        )
            else:
                users_text += "Достижения отсутствуют.\n"

            users_text += "\n"
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("Назад", callback_data="admin_back"))
        bot.send_message(call.message.chat.id, users_text.strip(), reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "edit_events")
    def edit_events(call):
        data = load_data()
        future_events = [
            event for event in data.get('activities', [])
            if datetime.strptime(event['date'], '%Y-%m-%d') >= datetime.now()
        ]

        if not future_events:
            bot.send_message(call.message.chat.id, "Нет предстоящих мероприятий.")
            return

        markup = InlineKeyboardMarkup(row_width=1)
        for event in future_events:
            markup.add(InlineKeyboardButton(
                f"{event['title']}",
                callback_data=f"view_event:{event['id']}"
            ))
        markup.add(InlineKeyboardButton("Назад", callback_data="admin_back"))

        bot.send_message(call.message.chat.id, "Предстоящие мероприятия:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("view_event"))
    def view_event(call):
        data = load_data()
        event_id = call.data.split(':')[1]

        event = next((event for event in data['activities'] if event.get('id') == event_id), None)

        if event is None:
            bot.send_message(call.message.chat.id, "Ошибка: мероприятие не найдено.")
            return

        text = (
            f"Название: {event['title']}\n"
            f"Описание: {event['description']}\n"
            f"Дата: {event['date']}\n"
            f"Место: {event['location']}"
        )

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Отредактировать", callback_data=f"edit_event:{event['id']}"),
            InlineKeyboardButton("Удалить", callback_data=f"delete_event:{event['id']}"),
            InlineKeyboardButton("Назад", callback_data="edit_events")
        )
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_event"))
    def edit_event(call):
        data = load_data()
        event_id = call.data.split(':')[1]

        event = next((event for event in data['activities'] if event.get('id') == event_id), None)

        if event is None:
            bot.send_message(call.message.chat.id, "Ошибка: мероприятие не найдено.")
            return

        msg = bot.send_message(call.message.chat.id, "Введите новое название мероприятия:")
        bot.register_next_step_handler(msg, get_new_description, event, call)

    def get_new_description(message, event, call):
        new_title = message.text.strip()
        msg = bot.send_message(message.chat.id, "Введите новое описание мероприятия:")
        bot.register_next_step_handler(msg, get_new_date, event, new_title, call)

    def get_new_date(message, event, new_title, call):
        new_description = message.text.strip()
        msg = bot.send_message(message.chat.id, "Введите новую дату мероприятия (ГГГГ-ММ-ДД):")
        bot.register_next_step_handler(msg, get_new_location, event, new_title, new_description, call)

    def get_new_location(message, event, new_title, new_description, call):
        new_date = message.text.strip()
        try:
            datetime.strptime(new_date, '%Y-%m-%d')
        except ValueError:
            msg = bot.send_message(message.chat.id, "Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД:")
            bot.register_next_step_handler(msg, get_new_location, event, new_title, new_description, call)
            return

        msg = bot.send_message(message.chat.id, "Введите новое место проведения мероприятия:")
        bot.register_next_step_handler(msg, update_event, event, new_title, new_description, new_date, call)

    def update_event(message, event, new_title, new_description, new_date, call):
        new_location = message.text.strip()

        event['title'] = new_title
        event['description'] = new_description
        event['date'] = new_date
        event['location'] = new_location

        data = load_data()

        for idx, existing_event in enumerate(data['activities']):
            if existing_event['id'] == event['id']:
                data['activities'][idx] = event
                break

        save_data(data)

        bot.send_message(message.chat.id, "Мероприятие обновлено.")
        edit_events(call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_event"))
    def delete_event(call):
        data = load_data()
        event_id = call.data.split(':')[1]

        data['activities'] = [
            event for event in data['activities'] if event['id'] != event_id
        ]

        save_data(data)
        bot.send_message(call.message.chat.id, "Мероприятие удалено.")
        edit_events(call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("view_students"))
    def view_students_callback(call):
        data = load_data()
        students = data.get('students', [])
        page = int(call.data.split(':')[1])
        display_student_buttons(call.message.chat.id, page, bot, students)

    def display_student_buttons(chat_id, page, bot, students):
        items_per_page = 3
        start = page * items_per_page
        end = start + items_per_page
        student_slice = students[start:end]

        if not student_slice:
            bot.send_message(chat_id, "Студенты закончились или страница пуста.")
            return

        markup = InlineKeyboardMarkup(row_width=1)
        for index, student in enumerate(student_slice, start=1):
            index_on_page = index + start
            button = InlineKeyboardButton(
                f"{index_on_page}. {student['last_name']} {student['first_name']} {student['group_number']}",
                callback_data=f"select_student:{index_on_page}:{page}"
            )
            markup.add(button)

        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"view_students:{page-1}"))
        if end < len(students):
            nav_buttons.append(InlineKeyboardButton("➡️ Вперёд", callback_data=f"view_students:{page+1}"))
        
        markup.add(*nav_buttons)
        markup.add(InlineKeyboardButton("Назад", callback_data="admin_back"))
        bot.send_message(chat_id, "Выберите студента для добавления в администраторы:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("select_student"))
    def select_student(call):
        data = load_data()
        students = data.get('students', [])
        _, index_on_page, _ = call.data.split(':')
        index_on_page = int(index_on_page) - 1

        if index_on_page < 0 or index_on_page >= len(students):
            bot.send_message(call.message.chat.id, "Ошибка: неверный индекс студента.")
            return

        selected_student = students[index_on_page]

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_add:{selected_student['telegram_id']}"),
            InlineKeyboardButton("❌ Нет", callback_data="admin_back")
        )

        text = (
            f"Сделать {selected_student['last_name']} {selected_student['first_name']} "
            f"администратором?"
        )
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_add"))
    def confirm_add_admin(call):
        data = load_data()
        selected_telegram_id = call.data.split(':')[1]

        student = next((s for s in data['students'] if str(s['telegram_id']) == selected_telegram_id), None)

        if not student:
            bot.send_message(call.message.chat.id, "Ошибка: студент не найден.")
            return

        new_admin = {
            "telegram_id": student['telegram_id'],
            "first_name": student['first_name'],
            "last_name": student['last_name'],
            "group_number": student['group_number']
        }

        already_admins = {admin['telegram_id'] for admin in data['admins']}
        if str(new_admin['telegram_id']) in map(str, already_admins):
            text = f"{new_admin['last_name']} {new_admin['first_name']} уже является администратором."
        else:
            data['admins'].append(new_admin)
            save_data(data)
            text = (
                f"Вы сделали {new_admin['last_name']} {new_admin['first_name']} "
                f"администратором."
            )

        bot.send_message(call.message.chat.id, text)
        send_admin_menu(call.message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == "approve_events")
    def approve_events(call):
        data = load_data()
        unconfirmed_events = [
            event for event in data.get('activities', []) if not event.get('confirmed', False)
        ]

        if not unconfirmed_events:
            bot.send_message(call.message.chat.id, "Нет мероприятий, ожидающих подтверждения.")
            return

        event_list_text = "Неподтверждённые мероприятия:\n" + "\n".join(
            [f"{index + 1}. {event['title']}" for index, event in enumerate(unconfirmed_events)]
        )

        markup = InlineKeyboardMarkup(row_width=1)
        for event in unconfirmed_events:
            markup.add(InlineKeyboardButton(
                f"{event['title']}",
                callback_data=f"review_event:{event['id']}"
            ))
        markup.add(InlineKeyboardButton("Назад", callback_data="admin_back"))

        bot.send_message(call.message.chat.id, event_list_text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("review_event"))
    def review_event(call):
        data = load_data()
        event_id = call.data.split(':')[1]

        event = next((event for event in data['activities'] if event.get('id') == event_id), None)

        if event is None:
            bot.send_message(call.message.chat.id, "Ошибка: мероприятие не найдено.")
            return

        text = (
            f"Название: {event['title']}\nОписание: {event['description']}\n"
            f"Дата: {event['date']}\nМесто: {event['location']}"
        )

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Подтвердить", callback_data=f"confirm_event:{event['id']}"),
            InlineKeyboardButton("Отклонить", callback_data=f"deny_event:{event['id']}"),
            InlineKeyboardButton("Редактировать", callback_data=f"edit_event:{event['id']}"),
            InlineKeyboardButton("Назад", callback_data="approve_events")
        )
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_event"))
    def confirm_event(call):
        data = load_data()
        event_id = call.data.split(':')[1]

        for event in data['activities']:
            if 'id' in event and event['id'] == event_id:
                event['confirmed'] = True
                save_data(data)
                bot.send_message(call.message.chat.id, "Мероприятие подтверждено.")
                approve_events(call)
                return

        bot.send_message(call.message.chat.id, "Ошибка: мероприятие не найдено.")
        handle_admin_back(call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("deny_event"))
    def deny_event(call):
        data = load_data()
        event_id = call.data.split(':')[1]

        data['activities'] = [
            event for event in data['activities'] if event['id'] != event_id
        ]

        save_data(data)
        bot.send_message(call.message.chat.id, "Мероприятие отклонено.")
        approve_events(call)

    @bot.callback_query_handler(func=lambda call: call.data == "approve_student_achievements")
    def approve_student_achievements(call):
        data = load_data()

        unconfirmed_achievements = [
            ach for ach in data.get('achievements', []) if not ach.get('confirmed', False)
        ]

        if not unconfirmed_achievements:
            bot.send_message(call.message.chat.id, "Нет достижений для подтверждения.")
            return

        event_dict = {event['id']: event['title'] for event in data.get('activities', [])}

        achievement_list_text = "Неподтверждённые достижения:\n"
        for index, ach in enumerate(unconfirmed_achievements, start=1):
            event_title = event_dict.get(ach['event_id'], "Мероприятие не найдено")
            achievement_list_text += (
                f"{index}. Студент ID {ach['student_id']} на мероприятии "
                f"{event_title} занял {ach['place']}\n"
            )

        markup = InlineKeyboardMarkup(row_width=1)
        for ach in unconfirmed_achievements:
            student_id = ach['student_id']
            event_id = ach['event_id']
            callback_data = f"review_ach:{student_id},{event_id}"

            if len(callback_data) <= 64:
                markup.add(InlineKeyboardButton(
                    f"Участник ID: {student_id} - {ach['place']}",
                    callback_data=callback_data
                ))
        markup.add(InlineKeyboardButton("Назад", callback_data="admin_back"))

        bot.send_message(call.message.chat.id, achievement_list_text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("review_ach"))
    def review_achievement(call):
        data = load_data()
        student_id, event_id = call.data.split(':')[1].split(',')
        student_id, event_id = str(student_id), str(event_id)

        achievement = next((ach for ach in data['achievements']
                            if str(ach['student_id']) == student_id and str(ach['event_id']) == event_id), None)

        if achievement is None:
            bot.send_message(call.message.chat.id, "Ошибка: достижение не найдено.")
            print(f"DEBUG: student_id={student_id}, event_id={event_id}, achievements={data['achievements']}")
            return

        text = (
            f"Студент ID: {student_id}\n"
            f"Мероприятие ID: {event_id}\n"
            f"Место: {achievement['place']}\n"
        )

        markup = InlineKeyboardMarkup(row_width=1)
        confirm_callback = f"confirm_ach:{student_id},{event_id}"

        if len(confirm_callback) <= 64:
            markup.add(
                InlineKeyboardButton("✅ Подтвердить", callback_data=confirm_callback),
            )

        markup.add(
            InlineKeyboardButton("❌ Отклонить", callback_data="cancel_action")
        )

        bot.send_message(call.message.chat.id, text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_ach"))
    def confirm_achievement(call):
        data = load_data()
        student_id, event_id = call.data.split(':')[1].split(',')
        student_id, event_id = str(student_id), str(event_id)

        for ach in data['achievements']:
            if str(ach['student_id']) == student_id and str(ach['event_id']) == event_id:
                ach['confirmed'] = True
                save_data(data)
                bot.send_message(call.message.chat.id, "Достижение успешно подтверждено!")
                return

        bot.send_message(call.message.chat.id, "Ошибка: достижение не найдено.")
