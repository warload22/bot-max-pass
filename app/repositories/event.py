from sqlalchemy.orm import Session
from datetime import date
from app.models import Event, Setting
from .base import BaseRepository

class EventRepository(BaseRepository):
    """Репозиторий для работы с мероприятиями."""

    def get_current(self) -> Event | None:
        """Возвращает текущее активное мероприятие."""
        setting = self.db.query(Setting).filter(Setting.key == 'current_event_id').first()
        if not setting or not setting.value:
            return None
        try:
            event_id = int(setting.value)
            return self.db.query(Event).filter(Event.id == event_id).first()
        except (ValueError, TypeError):
            return None

    def get_by_id(self, event_id: int) -> Event | None:
        """Возвращает мероприятие по ID."""
        return self.db.query(Event).filter(Event.id == event_id).first()

    def create(self, event_date: date, description: str, is_active: bool = False) -> Event:
        """Создаёт новое мероприятие."""
        event = Event(
            event_date=event_date,
            description=description,
            is_active=is_active,
            is_archived=False
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def update_date(self, event_id: int, new_date: date) -> None:
        """Обновляет дату мероприятия."""
        event = self.get_by_id(event_id)
        if event:
            event.event_date = new_date
            self.db.commit()

    def archive(self, event_id: int) -> None:
        """Помечает мероприятие как архивированное."""
        event = self.get_by_id(event_id)
        if event:
            event.is_archived = True
            event.is_active = False
            self.db.commit()

    def get_future_events(self) -> list[Event]:
        """Возвращает все будущие мероприятия (дата >= сегодня)."""
        today = date.today()
        return self.db.query(Event).filter(Event.event_date >= today).order_by(Event.event_date).all()

    def get_archived(self) -> list[Event]:
        """Возвращает все архивированные мероприятия."""
        return self.db.query(Event).filter(Event.is_archived == True).order_by(Event.event_date.desc()).all()