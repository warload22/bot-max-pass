from sqlalchemy.orm import Session
from app.models import Setting
from .base import BaseRepository

class SettingRepository(BaseRepository):
    """Репозиторий для работы с настройками."""

    def get(self, key: str) -> str | None:
        """Возвращает значение настройки по ключу."""
        setting = self.db.query(Setting).filter(Setting.key == key).first()
        return setting.value if setting else None

    def set(self, key: str, value: str, description: str = None) -> None:
        """Устанавливает значение настройки (создаёт или обновляет)."""
        setting = self.db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
            if description is not None:
                setting.description = description
        else:
            setting = Setting(key=key, value=value, description=description)
            self.db.add(setting)
        self.db.commit()

    def delete(self, key: str) -> None:
        """Удаляет настройку."""
        self.db.query(Setting).filter(Setting.key == key).delete()
        self.db.commit()