import logging
from typing import List

from app.core.database import SessionLocal
from app.handlers.common import States, CallbackActions, build_menu_keyboard
from app.services import max_api
from app.repositories.dialog_state import DialogStateRepository
from . import auth, stats, dates, logs, status, exports

logger = logging.getLogger(__name__)

def send_admin_menu(chat_id: int, user_id: int) -> None:
    """Отправляет главное меню администратора."""
    buttons = [
        ("📊 Статистика", CallbackActions.ADMIN_STATS),
        ("📅 Управление датами", CallbackActions.ADMIN_DATES),
        ("📋 Логи сервера", CallbackActions.ADMIN_LOGS),
        ("🖥 Статус сервера", CallbackActions.ADMIN_STATUS),
        ("📤 Выгрузить полные данные (Excel)", CallbackActions.ADMIN_EXPORT_FULL),
        ("📥 Архив мероприятий", CallbackActions.ADMIN_ARCHIVE),
        ("🚪 Выход", CallbackActions.ADMIN_LOGOUT)
    ]
    keyboard = build_menu_keyboard(buttons, row_width=2)
    max_api.send_message(chat_id, "Панель администратора. Выберите действие:", keyboard=keyboard)

def handle_admin_callback(chat_id: int, user_id: int, action: str, args: List[str]) -> None:
    """Обрабатывает callback'и из админ-меню."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        if action == CallbackActions.ADMIN_STATS:
            stats.send_statistics(chat_id, user_id)
        elif action == CallbackActions.ADMIN_DATES:
            dates.send_dates_menu(chat_id, user_id)
        elif action == CallbackActions.ADMIN_LOGS:
            logs.send_logs(chat_id, user_id)
        elif action == CallbackActions.ADMIN_STATUS:
            status.send_server_status(chat_id, user_id)
        elif action == CallbackActions.ADMIN_EXPORT_FULL:
            exports.export_full_data(chat_id, user_id)
        elif action == CallbackActions.ADMIN_ARCHIVE:
            exports.show_archive(chat_id, user_id)
        elif action == "archive_download":
            if args:
                exports.handle_archive_download(chat_id, user_id, args[0])
            else:
                max_api.send_message(chat_id, "Ошибка: не указано мероприятие.")
        elif action == CallbackActions.ADMIN_CHANGE_DATE:
            dates.handle_change_date(chat_id, user_id)
        elif action == CallbackActions.ADMIN_ADD_NEXT:
            dates.handle_add_next(chat_id, user_id)
        elif action == CallbackActions.ADMIN_BACK:
            dialog_repo.set(user_id, States.ADMIN_MENU)
            send_admin_menu(chat_id, user_id)
        elif action == CallbackActions.CANCEL_ADMIN:
            dialog_repo.set(user_id, States.ADMIN_MENU)
            send_admin_menu(chat_id, user_id)
        elif action == 'noop':
            pass
        elif action == CallbackActions.ADMIN_LOGOUT:
            auth.logout_admin(chat_id, user_id)
        else:
            max_api.send_message(chat_id, "Неизвестная команда.")
    finally:
        db.close()