from sqlalchemy.orm import Session

class BaseRepository:
    """Базовый класс для всех репозиториев."""
    def __init__(self, db: Session):
        self.db = db