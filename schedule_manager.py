# schedule_manager.py
"""
Модуль для планирования и отправки случайных сообщений.
Использует библиотеку schedule для периодического выполнения задач.
"""

import schedule
import time
import threading
import random
from data_manager import load_data
from ru import RAND_MESSAGES
from bot_instance import bot

def send_random_messages():
    """
    Отправляет случайное сообщение каждому зарегистрированному пользователю.
    Если бот заблокирован, ошибка перехватывается и логируется.
    """
    data = load_data()
    for student in data.get('students', []):
        telegram_id = student.get('telegram_id')
        first_name = student.get('first_name', '')
        random_message = random.choice(RAND_MESSAGES).format(name=first_name)
        try:
            bot.send_message(telegram_id, random_message)
        except Exception as e:
            # Логируем ошибку, чтобы понять, к какому пользователю проблема
            print(f"Не удалось отправить сообщение пользователю {telegram_id}: {e}")

def run_schedule():
    """
    Бесконечный цикл для проверки запланированных задач.
    """
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    """
    Инициализирует планировщик и запускает его в отдельном потоке.
    """
    schedule.every(3).days.do(send_random_messages)
    threading.Thread(target=run_schedule, daemon=True).start()
