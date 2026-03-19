import logging

from app.handlers.common import CallbackActions, build_menu_keyboard
from app.services import admin_service, max_api

logger = logging.getLogger(__name__)

def send_server_status(chat_id: int, user_id: int) -> None:
    """Отправляет информацию о состоянии сервера."""
    status = admin_service.get_server_status()
    message = (
        f"🖥 Статус сервера:\n\n"
        f"CPU: {status['cpu_percent']}%\n"
        f"RAM: {status['memory_percent']}%\n"
        f"Диск /: {status['disk_percent_root']}%\n"
        f"Диск /mnt: {status['disk_percent_mnt']}%\n"
        f"Последний бекап БД: {status['last_backup']}\n"
        f"Размер бекапов: {status['backup_size']}\n"
    )
    max_api.send_message(chat_id, message)
    # Кнопка назад
    back_keyboard = build_menu_keyboard([("🔙 Назад", CallbackActions.ADMIN_BACK)])
    max_api.send_message(chat_id, "Вернуться в меню администратора:", keyboard=back_keyboard)