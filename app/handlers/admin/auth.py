import logging
import time
from typing import Optional

from app.core.database import SessionLocal
from app.handlers.common import States, CallbackActions, build_menu_keyboard
from app.services import auth_service, max_api
from app.repositories.dialog_state import DialogStateRepository

logger = logging.getLogger(__name__)

def handle_admin_command(chat_id: int, user_id: int) -> None:
    """Обрабатывает команду /admin, запрашивает пароль."""
    logger.info(f"handle_admin_command called for user {user_id}")
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        dialog_repo.set(user_id, States.AWAITING_ADMIN_PASSWORD, {})
        max_api.send_message(chat_id, "Введите пароль администратора:")
    finally:
        db.close()

def handle_admin_password(chat_id: int, user_id: int, password: str, mid: Optional[str] = None) -> None:
    """Проверяет пароль и при успехе показывает меню администратора."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        if auth_service.verify_admin_password(password):
            dialog_repo.set(user_id, States.ADMIN_MENU)
            from .menu import send_admin_menu  # чтобы избежать циклических импортов
            send_admin_menu(chat_id, user_id)
            if mid:
                time.sleep(0.5)
                max_api.delete_message(chat_id, mid)
        else:
            max_api.send_message(chat_id, "Неверный пароль. Доступ запрещён.")
            dialog_repo.clear(user_id)
    finally:
        db.close()

def logout_admin(chat_id: int, user_id: int) -> None:
    """Выход из админ-панели в главное меню пользователя."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        dialog_repo.clear(user_id)
        from app.handlers.message_handler import send_main_menu
        send_main_menu(chat_id, user_id)
    finally:
        db.close()