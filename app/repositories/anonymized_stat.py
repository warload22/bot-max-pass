from sqlalchemy.orm import Session
from app.models import AnonymizedStat
from .base import BaseRepository

class AnonymizedStatRepository(BaseRepository):
    """Репозиторий для работы с обезличенной статистикой."""

    def create(
        self,
        event_id: int,
        birth_year: int,
        birth_place: str,
        residence: str,
        category: str,
        education_interest: str,
        scan_status: str = None,
        school: str = None,
        is_russian_citizen: bool = None,
        registered_at=None
    ) -> AnonymizedStat:
        """Создаёт запись в anonymized_stats."""
        stat = AnonymizedStat(
            event_id=event_id,
            birth_year=birth_year,
            birth_place=birth_place,
            residence=residence,
            category=category,
            education_interest=education_interest,
            scan_status=scan_status,
            school=school,
            is_russian_citizen=is_russian_citizen,
            registered_at=registered_at
        )
        self.db.add(stat)
        self.db.commit()
        self.db.refresh(stat)
        return stat

    def get_by_event(self, event_id: int) -> list[AnonymizedStat]:
        """Возвращает все записи для мероприятия."""
        return self.db.query(AnonymizedStat).filter(AnonymizedStat.event_id == event_id).order_by(AnonymizedStat.registered_at).all()

    def delete_by_event(self, event_id: int) -> None:
        """Удаляет все записи для мероприятия."""
        self.db.query(AnonymizedStat).filter(AnonymizedStat.event_id == event_id).delete()
        self.db.commit()