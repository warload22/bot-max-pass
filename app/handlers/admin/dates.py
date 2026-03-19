import logging
from datetime import datetime

from app.core.database import SessionLocal
from app.handlers.common import States, CallbackActions, build_menu_keyboard
from app.services import max_api
from app.repositories.dialog_state import DialogStateRepository
from app.repositories.event import EventRepository
from app.models import Event

logger = logging.getLogger(__name__)

def send_dates_menu(chat_id: int, user_id: int) -> None:
    """Показывает меню управления датами."""
    db = SessionLocal()
    try:
        event_repo = EventRepository(db)
        event = event_repo.get_current()
        current_date_str = event.event_date.strftime('%d.%m.%Y') if event else "не установлена"
        buttons = [
            (f"Текущая дата: {current_date_str}", "noop"),
            ("✏️ Изменить дату текущего мероприятия", CallbackActions.ADMIN_CHANGE_DATE),
            ("➕ Запланировать следующее мероприятие", CallbackActions.ADMIN_ADD_NEXT),
            ("🔙 Назад", CallbackActions.ADMIN_BACK)
        ]
        keyboard = build_menu_keyboard(buttons, row_width=1)
        max_api.send_message(chat_id, "Управление датами:", keyboard=keyboard)
    finally:
        db.close()

def handle_change_date(chat_id: int, user_id: int) -> None:
    """Запрашивает новую дату для текущего мероприятия."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        dialog_repo.set(user_id, States.ADMIN_AWAITING_NEW_DATE)
        keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL_ADMIN)])
        max_api.send_message(chat_id, "Введите новую дату в формате ДД.ММ.ГГГГ (или нажмите «Отмена»):", keyboard=keyboard)
    finally:
        db.close()

def handle_new_date_input(chat_id: int, user_id: int, text: str) -> None:
    """Обрабатывает ввод новой даты, обновляет мероприятие."""
    try:
        new_date = datetime.strptime(text.strip(), "%d.%m.%Y").date()
    except ValueError:
        max_api.send_message(chat_id, "Неверный формат. Введите дату в формате ДД.ММ.ГГГГ:")
        return
    db = SessionLocal()
    try:
        event_repo = EventRepository(db)
        dialog_repo = DialogStateRepository(db)
        event = event_repo.get_current()
        if not event:
            max_api.send_message(chat_id, "Ошибка: нет активного мероприятия.")
            dialog_repo.clear(user_id)
            return
        event.event_date = new_date
        db.commit()
        max_api.send_message(chat_id, f"Дата мероприятия изменена на {new_date.strftime('%d.%m.%Y')}.")
        from .menu import send_admin_menu
        dialog_repo.set(user_id, States.ADMIN_MENU)
        send_admin_menu(chat_id, user_id)
    finally:
        db.close()

def handle_add_next(chat_id: int, user_id: int) -> None:
    """Запрашивает дату следующего мероприятия."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        dialog_repo.set(user_id, States.ADMIN_AWAITING_NEXT_EVENT_DATE)
        keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL_ADMIN)])
        max_api.send_message(chat_id, "Введите дату следующего мероприятия в формате ДД.ММ.ГГГГ (или нажмите «Отмена»):", keyboard=keyboard)
    finally:
        db.close()

def handle_next_event_date_input(chat_id: int, user_id: int, text: str) -> None:
    """Создаёт новое мероприятие с указанной датой."""
    try:
        new_date = datetime.strptime(text.strip(), "%d.%m.%Y").date()
    except ValueError:
        max_api.send_message(chat_id, "Неверный формат. Введите дату в формате ДД.ММ.ГГГГ:")
        return
    db = SessionLocal()
    try:
        event_repo = EventRepository(db)
        dialog_repo = DialogStateRepository(db)
        existing = event_repo.get_by_id(event_repo.get_current().id)  # не совсем правильно
        # Лучше проверить, нет ли уже мероприятия с такой датой
        existing = db.query(Event).filter(Event.event_date == new_date).first()
        if existing:
            max_api.send_message(chat_id, "Мероприятие с такой датой уже существует.")
            return
        event_repo.create(
            event_date=new_date,
            description=f"День открытых дверей {new_date.strftime('%d.%m.%Y')}",
            is_active=False
        )
        max_api.send_message(chat_id, f"Следующее мероприятие на {new_date.strftime('%d.%m.%Y')} создано.")
        from .menu import send_admin_menu
        dialog_repo.set(user_id, States.ADMIN_MENU)
        send_admin_menu(chat_id, user_id)
    finally:
        db.close()