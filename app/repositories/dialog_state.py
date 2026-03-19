from sqlalchemy.orm import Session
from datetime import datetime
from app.models import DialogState
from .base import BaseRepository

class DialogStateRepository(BaseRepository):
    """Репозиторий для работы с состояниями диалогов."""

    def get(self, user_id: int) -> tuple[int | None, dict | None]:
        """Возвращает состояние и данные пользователя."""
        dialog = self.db.query(DialogState).filter(DialogState.user_id == user_id).first()
        if dialog:
            return dialog.state, dialog.data
        return None, None

    def set(self, user_id: int, state: int, data: dict = None) -> None:
        """Устанавливает состояние диалога для пользователя."""
        dialog = self.db.query(DialogState).filter(DialogState.user_id == user_id).first()
        if dialog:
            dialog.state = state
            if data is not None:
                dialog.data = data
            dialog.updated_at = datetime.now()
        else:
            dialog = DialogState(user_id=user_id, state=state, data=data)
            self.db.add(dialog)
        self.db.commit()

    def clear(self, user_id: int) -> None:
        """Удаляет состояние диалога для пользователя."""
        self.db.query(DialogState).filter(DialogState.user_id == user_id).delete()
        self.db.commit()

    def update_data(self, user_id: int, **kwargs) -> None:
        """Обновляет только поле data, добавляя новые ключи."""
        dialog = self.db.query(DialogState).filter(DialogState.user_id == user_id).first()
        if dialog:
            if dialog.data is None:
                dialog.data = {}
            dialog.data.update(kwargs)
            dialog.updated_at = datetime.now()
            self.db.commit()