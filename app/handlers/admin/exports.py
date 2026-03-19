import logging

from app.core.database import SessionLocal
from app.handlers.common import CallbackActions, build_menu_keyboard, build_callback_data
from app.services import export_service, admin_service, max_api
from app.repositories.event import EventRepository

logger = logging.getLogger(__name__)

def export_full_data(chat_id: int, user_id: int) -> None:
    """Генерирует и отправляет Excel с полными данными."""
    db = SessionLocal()
    try:
        event_repo = EventRepository(db)
        event = event_repo.get_current()
        if not event:
            max_api.send_message(chat_id, "Нет активного мероприятия.")
            return
        file_bytes = export_service.export_full_registrations(db, event.id)
        if not file_bytes:
            max_api.send_message(chat_id, "Нет данных для выгрузки.")
            return
        filename = f"registrations_{event.event_date.strftime('%Y%m%d')}.xlsx"
        max_api.send_document(chat_id, file_bytes, filename, caption="Полные данные регистрации")
        # Кнопка назад
        back_keyboard = build_menu_keyboard([("🔙 Назад", CallbackActions.ADMIN_BACK)])
        max_api.send_message(chat_id, "Вернуться в меню администратора:", keyboard=back_keyboard)
    except Exception as e:
        logger.error(f"Export error: {e}")
        max_api.send_message(chat_id, "Ошибка при выгрузке данных.")
    finally:
        db.close()

def show_archive(chat_id: int, user_id: int) -> None:
    """Показывает список прошедших мероприятий для выгрузки статистики."""
    db = SessionLocal()
    try:
        events = admin_service.get_archived_events(db)
        if not events:
            max_api.send_message(chat_id, "Архив пуст.")
            return
        buttons = []
        for ev in events:
            callback = build_callback_data(CallbackActions.ADMIN_ARCHIVE_DOWNLOAD, ev.id)
            buttons.append((ev.event_date.strftime('%d.%m.%Y'), callback))
        buttons.append(("🔙 Назад", CallbackActions.ADMIN_BACK))
        keyboard = build_menu_keyboard(buttons, row_width=2)
        max_api.send_message(chat_id, "Выберите мероприятие для скачивания обезличенной статистики:", keyboard=keyboard)
    finally:
        db.close()

def handle_archive_download(chat_id: int, user_id: int, event_id: str) -> None:
    """Обрабатывает скачивание обезличенной статистики для выбранного мероприятия."""
    db = SessionLocal()
    try:
        file_bytes = export_service.export_anonymized_stats(db, int(event_id))
        if not file_bytes:
            max_api.send_message(chat_id, "Нет данных для этого мероприятия.")
            return
        filename = f"stats_anonymized_{event_id}.xlsx"
        max_api.send_document(chat_id, file_bytes, filename, caption="Обезличенная статистика")
        # Кнопка назад
        back_keyboard = build_menu_keyboard([("🔙 Назад", CallbackActions.ADMIN_BACK)])
        max_api.send_message(chat_id, "Вернуться в меню администратора:", keyboard=back_keyboard)
    except Exception as e:
        logger.error(f"Archive download error: {e}")
        max_api.send_message(chat_id, "Ошибка при выгрузке.")
    finally:
        db.close()