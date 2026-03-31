import uuid
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models import Registration
from .base import BaseRepository

class RegistrationRepository(BaseRepository):
    """Репозиторий для работы с регистрациями."""

    def create(
        self,
        event_id: int,
        full_name: str,
        birth_year: int,            # вместо birth_date
        birth_place: str,
        residence: str,
        email: str,
        category: str,
        education_interest: str,
        school: str = None,
        is_russian_citizen: bool = None
    ) -> Registration:
        """Создаёт новую регистрацию."""
        reg = Registration(
            event_id=event_id,
            full_name=full_name,
            birth_year=birth_year,
            birth_place=birth_place,
            residence=residence,
            email=email,
            category=category,
            education_interest=education_interest,
            school=school,
            is_russian_citizen=is_russian_citizen,
            is_active=True
        )
        self.db.add(reg)
        self.db.commit()
        self.db.refresh(reg)
        return reg

    def get_by_uuid(self, reg_uuid: uuid.UUID) -> Registration | None:
        """Возвращает регистрацию по UUID."""
        return self.db.query(Registration).filter(Registration.id == reg_uuid).first()

    def deactivate_old_by_email(self, email: str, event_id: int) -> None:
        """Деактивирует все активные регистрации пользователя на мероприятие."""
        self.db.query(Registration).filter(
            Registration.email == email,
            Registration.event_id == event_id,
            Registration.is_active == True
        ).update({"is_active": False})
        self.db.commit()

    def update_last_qr_sent(self, reg_uuid: uuid.UUID) -> None:
        """Обновляет время последней отправки QR-кода."""
        reg = self.get_by_uuid(reg_uuid)
        if reg:
            reg.last_qr_sent_at = datetime.now()
            self.db.commit()

    def get_active_by_email_and_event(self, email: str, event_id: int) -> Registration | None:
        """Возвращает активную регистрацию по email и мероприятию."""
        return self.db.query(Registration).filter(
            Registration.email == email,
            Registration.event_id == event_id,
            Registration.is_active == True
        ).first()

    def get_all_by_event(self, event_id: int) -> list[Registration]:
        """Возвращает все регистрации на мероприятие."""
        return self.db.query(Registration).filter(Registration.event_id == event_id).all()