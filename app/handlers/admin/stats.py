import logging

from app.core.database import SessionLocal
from app.handlers.common import CallbackActions, build_menu_keyboard, get_category_display, get_education_display
from app.services import admin_service, max_api
from app.repositories.event import EventRepository

logger = logging.getLogger(__name__)

def send_statistics(chat_id: int, user_id: int) -> None:
    """Отправляет статистику по текущему мероприятию."""
    db = SessionLocal()
    try:
        event_repo = EventRepository(db)
        event = event_repo.get_current()
        if not event:
            max_api.send_message(chat_id, "Нет активного мероприятия.")
            return
        stats = admin_service.get_statistics(db, event.id)
        if not stats:
            max_api.send_message(chat_id, "Не удалось получить статистику.")
            return
        message = (
            f"📊 Статистика по мероприятию {event.event_date.strftime('%d.%m.%Y')}:\n\n"
            f"Всего регистраций: {stats['total_registrations']}\n"
            f"Активных: {stats['active_registrations']}\n"
            f"Пропущено: {stats['scans_admitted']}\n"
            f"Не пропущено: {stats['scans_denied']}\n"
            f"Ожидают сканирования: {stats['scans_pending']}\n\n"
            f"По категориям:\n"
        )
        for cat, count in stats['by_category'].items():
            cat_display = get_category_display(cat)
            message += f"  {cat_display}: {count}\n"
        message += "\nПо интересам:\n"
        for edu, count in stats['by_education'].items():
            edu_display = get_education_display(edu)
            message += f"  {edu_display}: {count}\n"
        max_api.send_message(chat_id, message)
        # Кнопка назад
        back_keyboard = build_menu_keyboard([("🔙 Назад", CallbackActions.ADMIN_BACK)])
        max_api.send_message(chat_id, "Вернуться в меню администратора:", keyboard=back_keyboard)
    finally:
        db.close()