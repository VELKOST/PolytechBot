# handlers/events.py

import uuid
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot
from data_manager import load_data, save_data
from handlers.statistics import send_statistics_options

@bot.callback_query_handler(func=lambda call: call.data == "show_achievements")
def show_achievements(call):
    """
    Обрабатывает команду "Похвастаться" для регистрации достижения.
    """
    bot.answer_callback_query(call.id)
    telegram_id = call.from_user.id
    data = load_data()
    student = next((s for s in data.get('students', []) if s['telegram_id'] == telegram_id), None)
    if student:
        past_events = [a for a in data.get('activities', []) if a.get('confirmed', False)]
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
    """
    Обрабатывает выбор мероприятия для добавления достижения.
    """
    event_id = call.data.split("_")[-1]
    msg = bot.send_message(call.message.chat.id, "Введите место, которое вы заняли (1-е, 2-е, 3-е место и т.д.):")
    bot.register_next_step_handler(msg, get_achievement_result, event_id)

def get_achievement_result(message, event_id):
    """
    Получает результат достижения от пользователя и сохраняет его.
    """
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
    data = load_data()
    data.setdefault('achievements', []).append(achievement)
    save_data(data)
    bot.send_message(message.chat.id, "Ваше достижение успешно передано администрации!")
    send_statistics_options(message)


import io
from fpdf import FPDF
import os


# Добавим функцию для генерации PDF
def generate_pdf(events):
    pdf = FPDF()
    pdf.add_page()

    # Путь к шрифту
    font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf')

    # Проверяем, существует ли файл шрифта
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Шрифт не найден: {font_path}")

    # Добавляем шрифт с поддержкой кириллицы (нужен файл DejaVuSans.ttf в директории)
    pdf.add_font('DejaVu', '', font_path, uni=True)
    pdf.set_font('DejaVu', '', 12)

    pdf.cell(200, 10, txt="Ваши мероприятия", ln=1, align='C')

    for event in events:
        title = event.get('title', 'Без названия')
        description = event.get('description', 'Описание отсутствует')
        date = event.get('date', 'Дата не указана')
        level = event.get('event_level', 'Не указан')
        category = event.get('event_category', 'Не указана')

        text = (
            f"Название: {title}\n"
            f"Описание: {description}\n"
            f"Дата: {date}\n"
            f"Уровень: {level}\n"
            f"Категория: {category}\n\n"
        )
        pdf.multi_cell(0, 10, txt=text)

    return pdf.output(dest='S').encode('latin1')


@bot.callback_query_handler(func=lambda call: call.data == "my_events")
def show_my_events(call):
    bot.answer_callback_query(call.id)
    telegram_id = call.from_user.id
    data = load_data()

    student = next((s for s in data.get('students', []) if s['telegram_id'] == telegram_id), None)
    if not student:
        bot.send_message(call.message.chat.id, "Пожалуйста, сначала зарегистрируйтесь.")
        return

    achievements = [ach for ach in data.get('achievements', []) if ach['student_id'] == student['telegram_id']]
    events = []
    for ach in achievements:
        event = next((e for e in data.get('activities', []) if e['id'] == ach['event_id']), None)
        if event:
            events.append(event)

    if not events:
        events_text = "У вас пока нет зарегистрированных мероприятий."
    else:
        events_text = "Ваши мероприятия:\n\n"
        for event in events:
            events_text += (
                f"Название: {event['title']}\n"
                f"Описание: {event['description']}\n"
                f"Дата: {event['date']}\n"
                f"Уровень: {event.get('event_level', 'Не указан')}\n"
                f"Категория: {event.get('event_category', 'Не указана')}\n\n"
            )

    markup = InlineKeyboardMarkup(row_width=1)
    if events:
        markup.add(
            InlineKeyboardButton("Скачать PDF", callback_data="generate_pdf"),
            InlineKeyboardButton("Назад", callback_data="back_to_statistics")
        )
    else:
        markup.add(InlineKeyboardButton("Назад", callback_data="back_to_statistics"))

    bot.send_message(call.message.chat.id, events_text, reply_markup=markup)


# Обработчик для генерации PDF
@bot.callback_query_handler(func=lambda call: call.data == "generate_pdf")
def handle_generate_pdf(call):
    bot.answer_callback_query(call.id)
    telegram_id = call.from_user.id
    data = load_data()

    student = next((s for s in data.get('students', []) if s['telegram_id'] == telegram_id), None)
    if not student:
        bot.send_message(call.message.chat.id, "Пользователь не найден.")
        return

    achievements = [ach for ach in data.get('achievements', []) if ach['student_id'] == student['telegram_id']]
    events = []
    for ach in achievements:
        event = next((e for e in data.get('activities', []) if e['id'] == ach['event_id']), None)
        if event:
            events.append(event)

    if not events:
        bot.send_message(call.message.chat.id, "Нет мероприятий для генерации PDF.")
        return

    try:
        # Генерируем PDF
        pdf_output = generate_pdf(events)
        # Создаем файловый объект в памяти
        pdf_file = io.BytesIO(pdf_output)
        pdf_file.seek(0)
        pdf_file.name = "my_events.pdf"

        # Отправляем документ
        bot.send_document(
            chat_id=call.message.chat.id,
            document=pdf_file,
            caption="Список ваших мероприятий"
        )
    except Exception as e:
        print(f"Ошибка при генерации PDF: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка при генерации отчета.")

@bot.callback_query_handler(func=lambda call: call.data == "upcoming_events")
def handle_upcoming_events(call):
    """
    Обрабатывает команду для отображения меню мероприятий.
    """
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
    """
    Отображает список предстоящих мероприятий.
    """
    data = load_data()
    activities = data.get('activities', [])
    current_date = datetime.now()
    upcoming_events = []
    for event in activities:
        try:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d')
            if event.get('confirmed', False) and event_date >= current_date:
                upcoming_events.append(event)
        except ValueError:
            continue
    if not upcoming_events:
        events_text = "На данный момент предстоящих мероприятий нет."
    else:
        events_text = "Предстоящие мероприятия:\n\n"
        for event in upcoming_events:
            events_text += (
                f"Название: {event['title']}\n"
                f"Описание: {event['description']}\n"
                f"Дата: {event['date']}\n"
                f"Место: {event['location']}\n"
                f"Уровень: {event.get('event_level', 'Не указан')}\n"
                f"Категория: {event.get('event_category', 'Не указана')}\n"
                f"Ссылка на опросник: {event.get('survey_link', 'Нет ссылки')}\n\n"
            )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("Назад", callback_data="back_to_upcoming_events"))
    bot.send_message(call.message.chat.id, events_text.strip(), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "report_event")
def report_event(call):
    """
    Запускает процесс подачи информации о новом мероприятии.
    """
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "Введите название мероприятия:")
    bot.register_next_step_handler(msg, get_activity_description_title)

def get_activity_description_title(message):
    """
    Получает название мероприятия от пользователя.
    """
    activity_title = message.text.strip()
    if not activity_title:
        msg = bot.send_message(message.chat.id, "Название мероприятия не может быть пустым. Пожалуйста, введите название:")
        bot.register_next_step_handler(msg, get_activity_description_title)
        return
    msg = bot.send_message(message.chat.id, "Введите описание мероприятия:")
    bot.register_next_step_handler(msg, get_activity_description, activity_title)

def get_activity_description(message, activity_title):
    """
    Получает описание мероприятия.
    """
    activity_description = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введите дату проведения мероприятия (ГГГГ-ММ-ДД):")
    bot.register_next_step_handler(msg, get_activity_date, activity_title, activity_description)

def get_activity_date(message, activity_title, activity_description):
    """
    Получает дату проведения мероприятия и проверяет формат.
    """
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
    """
    Получает место проведения мероприятия.
    """
    activity_location = message.text.strip()
    if not activity_location:
        msg = bot.send_message(message.chat.id, "Место проведения не может быть пустым. Пожалуйста, введите место:")
        bot.register_next_step_handler(msg, get_activity_location, activity_title, activity_description, activity_date)
        return
    msg = bot.send_message(message.chat.id, "Введите ссылку на опросник для мероприятия:")
    bot.register_next_step_handler(
        msg, get_event_level,
        activity_title, activity_description, activity_date, activity_location
    )

def get_event_level(message, activity_title, activity_description, activity_date, activity_location):
    """
    Запрашивает уровень мероприятия (локальный, региональный, всероссийский, международный).
    """
    survey_link = message.text.strip()
    if not survey_link:
        msg = bot.send_message(message.chat.id, "Ссылка на опросник не может быть пустой. Пожалуйста, введите ссылку:")
        bot.register_next_step_handler(msg, get_event_level, activity_title, activity_description, activity_date, activity_location)
        return

    # Сохраняем survey_link, продолжаем запрос уровня
    msg = bot.send_message(
        message.chat.id,
        "Введите уровень мероприятия (например, локальный, региональный, всероссийский, международный):"
    )
    bot.register_next_step_handler(
        msg, get_event_category,
        activity_title, activity_description, activity_date, activity_location, survey_link
    )

def get_event_category(message, activity_title, activity_description, activity_date, activity_location, survey_link):
    """
    Запрашивает категорию мероприятия (например, научная конференция, олимпиада, спортивное, и т. д.).
    """
    event_level = message.text.strip()
    if not event_level:
        msg = bot.send_message(message.chat.id, "Уровень мероприятия не может быть пустым. Пожалуйста, введите уровень:")
        bot.register_next_step_handler(
            msg, get_event_category,
            activity_title, activity_description, activity_date, activity_location, survey_link
        )
        return

    msg = bot.send_message(
        message.chat.id,
        "Введите категорию мероприятия (например, научная конференция, олимпиада, спортивное и т. д.):"
    )
    bot.register_next_step_handler(
        msg, save_activity_with_survey,
        activity_title, activity_description, activity_date, activity_location, survey_link, event_level
    )

def save_activity_with_survey(message, activity_title, activity_description, activity_date, activity_location, survey_link, event_level):
    """
    Сохраняет всю информацию о мероприятии, включая ссылку, уровень и категорию.
    """
    event_category = message.text.strip()
    if not event_category:
        msg = bot.send_message(message.chat.id, "Категория мероприятия не может быть пустой. Пожалуйста, введите категорию:")
        bot.register_next_step_handler(
            msg, save_activity_with_survey,
            activity_title, activity_description, activity_date, activity_location, survey_link, event_level
        )
        return

    new_activity = {
        'id': str(uuid.uuid4()),
        'title': activity_title,
        'description': activity_description,
        'date': activity_date,
        'location': activity_location,
        'survey_link': survey_link,
        'event_level': event_level,
        'event_category': event_category,
        'confirmed': False,
        'submitter_id': message.from_user.id
    }
    data = load_data()
    data.setdefault('activities', []).append(new_activity)
    save_data(data)
    bot.send_message(message.chat.id, "Информация о мероприятии успешно сохранена и ожидает подтверждения.")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_upcoming_events")
def back_to_upcoming_events(call):
    """
    Обрабатывает кнопку "Назад" в меню предстоящих мероприятий.
    """
    handle_upcoming_events(call)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_welcome")
def handle_back_to_welcome(call):
    """
    Возвращает пользователя к главному меню.
    """
    from handlers.main_handlers import send_welcome
    send_welcome(call.message)
