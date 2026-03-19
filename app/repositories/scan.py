import uuid
from sqlalchemy.orm import Session
from app.models import Scan
from .base import BaseRepository

class ScanRepository(BaseRepository):
    """Репозиторий для работы со сканированиями."""

    def create(self, registration_id: uuid.UUID, status: str, scanned_by: str = None, comment: str = None) -> Scan:
        """Записывает новое сканирование."""
        scan = Scan(
            registration_id=registration_id,
            status=status,
            scanned_by=scanned_by,
            comment=comment
        )
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def get_last_by_registration(self, registration_id: uuid.UUID) -> Scan | None:
        """Возвращает последнее сканирование для регистрации."""
        return self.db.query(Scan).filter(
            Scan.registration_id == registration_id
        ).order_by(Scan.id.desc()).first()

    def get_all_by_registration(self, registration_id: uuid.UUID) -> list[Scan]:
        """Возвращает все сканирования для регистрации."""
        return self.db.query(Scan).filter(
            Scan.registration_id == registration_id
        ).order_by(Scan.id.desc()).all()

    def count_by_status(self, registration_id: uuid.UUID, status: str) -> int:
        """Возвращает количество сканирований с указанным статусом для регистрации."""
        return self.db.query(Scan).filter(
            Scan.registration_id == registration_id,
            Scan.status == status
        ).count()