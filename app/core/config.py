import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # База данных
    LOCAL_DB_HOST = os.getenv('LOCAL_DB_HOST')
    LOCAL_DB_PORT = os.getenv('LOCAL_DB_PORT')
    LOCAL_DB_NAME = os.getenv('LOCAL_DB_NAME')
    LOCAL_DB_USER = os.getenv('LOCAL_DB_USER')
    LOCAL_DB_PASSWORD = os.getenv('LOCAL_DB_PASSWORD')

    # Токен бота MAX
    MAX_BOT_TOKEN = os.getenv('MAX_BOT_TOKEN')

    # Секретный ключ приложения
    APP_SECRET = os.getenv('APP_SECRET')

    # Базовый URL для QR-кодов
    QR_BASE_URL = os.getenv('QR_BASE_URL')

    # Режим отладки
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # Смещение времени в секундах (например, +10800 для UTC+3)
    TIME_OFFSET = int(os.getenv('TIME_OFFSET', '0'))

    # Флаг для secure cookie (в production true, в разработке false)
    SECURE_COOKIE = not DEBUG

    # Пути
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    BACKUP_DIR = os.path.join(BASE_DIR, 'backups')