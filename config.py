# config.py
"""
Конфигурационный файл для бота.
Здесь хранятся настройки и параметры, например, токен.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из файла .env

TOKEN = os.getenv("TOKEN")  # Токен бота
