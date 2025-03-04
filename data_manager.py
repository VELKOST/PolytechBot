# data_manager.py
"""
Модуль для работы с данными.
Содержит функции загрузки и сохранения данных, а также вспомогательные функции для работы с JSON.
"""

import json

DATA_FILENAME = 'basa.json'

def load_data(filename=DATA_FILENAME):
    """
    Загружает данные из JSON-файла.
    Если файл не найден или повреждён, возвращает пустую структуру данных.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Проверяем наличие необходимых ключей
            for key in ['students', 'activities', 'achievements', 'admins']:
                if key not in data:
                    data[key] = []
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {'students': [], 'activities': [], 'achievements': [], 'admins': []}

def save_data(data, filename=DATA_FILENAME):
    """
    Сохраняет данные в JSON-файл.
    """
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def is_user_registered(telegram_id, data):
    """
    Проверяет, зарегистрирован ли пользователь по его telegram_id.
    """
    return any(student['telegram_id'] == telegram_id for student in data.get('students', []))

def add_student(data, telegram_id, first_name, last_name, group_number):
    """
    Добавляет нового студента в данные и сохраняет их.
    """
    new_student = {
        'telegram_id': telegram_id,
        'first_name': first_name,
        'last_name': last_name,
        'group_number': group_number
    }
    data.setdefault('students', []).append(new_student)
    save_data(data)
