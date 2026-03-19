import logging
import os

from app.core.config import Config
from app.handlers.common import CallbackActions, build_menu_keyboard
from app.services import max_api

logger = logging.getLogger(__name__)

def send_logs(chat_id: int, user_id: int) -> None:
    """Отправляет последние 50 строк из лога."""
    log_file = os.path.join(Config.LOG_DIR, 'app.log')
    if not os.path.exists(log_file):
        max_api.send_message(chat_id, "Файл логов не найден.")
        return
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()[-50:]
        if not lines:
            max_api.send_message(chat_id, "Лог пуст.")
            return
        text = "".join(lines)
        if len(text) > 3500:
            text = text[-3500:] + "\n... (обрезано)"
        max_api.send_message(chat_id, f"Последние строки лога:\n```\n{text}\n```")
        # Кнопка назад
        back_keyboard = build_menu_keyboard([("🔙 Назад", CallbackActions.ADMIN_BACK)])
        max_api.send_message(chat_id, "Вернуться в меню администратора:", keyboard=back_keyboard)
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        max_api.send_message(chat_id, "Ошибка при чтении лога.")