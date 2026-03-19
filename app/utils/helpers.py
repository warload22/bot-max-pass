import re
from datetime import datetime
from typing import Optional

# Импортируем константы из common (пока оставим там)
from app.handlers.common import CATEGORIES, EDUCATION_INTERESTS, CALLBACK_SEPARATOR

def format_date_for_display(date_obj: datetime.date) -> str:
    """Форматирует дату в ДД.ММ.ГГГГ для отображения пользователю."""
    return date_obj.strftime("%d.%m.%Y")

def get_category_display(value: Optional[str]) -> str:
    """Возвращает отображаемое название категории по коду из БД."""
    mapping = dict(CATEGORIES)
    rev_mapping = {v: k for k, v in mapping.items()}
    return rev_mapping.get(value, value) if value else ''

def get_education_display(value: Optional[str]) -> str:
    """Возвращает отображаемое название интереса по коду из БД."""
    mapping = dict(EDUCATION_INTERESTS)
    rev_mapping = {v: k for k, v in mapping.items()}
    return rev_mapping.get(value, value) if value else ''

def validate_email(email: str) -> bool:
    """Проверяет корректность формата email."""
    return bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', email.strip().lower()))

def build_menu_keyboard(buttons, row_width=2):
    """
    Строит inline-клавиатуру для MAX.
    buttons: список строк или кортежей (текст, callback_data).
    """
    keyboard_rows = []
    current_row = []
    for i, btn in enumerate(buttons):
        if isinstance(btn, (tuple, list)):
            text, callback = btn
        else:
            text = btn
            callback = btn
        button = {
            "type": "callback",
            "text": text,
            "payload": callback
        }
        current_row.append(button)
        if (i + 1) % row_width == 0:
            keyboard_rows.append(current_row)
            current_row = []
    if current_row:
        keyboard_rows.append(current_row)
    return {
        "type": "inline_keyboard",
        "payload": {
            "buttons": keyboard_rows
        }
    }

def build_callback_data(action, *args):
    """Формирует строку callback_data из действия и аргументов."""
    return CALLBACK_SEPARATOR.join([str(action)] + [str(arg) for arg in args])

def parse_callback_data(data):
    """Разбирает callback_data на составляющие."""
    parts = data.split(CALLBACK_SEPARATOR)
    if not parts:
        return None, []
    return parts[0], parts[1:]