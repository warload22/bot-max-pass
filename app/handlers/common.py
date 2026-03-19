# Состояния диалога
class States:
    MAIN_MENU = 0
    AWAITING_ADMIN_PASSWORD = 1
    AWAITING_FULL_NAME = 10
    AWAITING_BIRTH_DATE = 11
    AWAITING_BIRTH_PLACE = 12
    AWAITING_RESIDENCE = 13
    AWAITING_EMAIL = 14
    AWAITING_CATEGORY = 15
    AWAITING_SCHOOL = 16
    AWAITING_EDUCATION_INTEREST = 17
    CONFIRM_DATA = 18
    ADMIN_MENU = 20
    ADMIN_AWAITING_NEW_DATE = 21
    ADMIN_AWAITING_NEXT_EVENT_DATE = 22
    AFTER_REGISTRATION = 30

# Callback-действия
class CallbackActions:
    REGISTER = "register"
    ADMIN_STATS = "admin_stats"
    ADMIN_DATES = "admin_dates"
    ADMIN_LOGS = "admin_logs"
    ADMIN_STATUS = "admin_status"
    ADMIN_EXPORT_FULL = "admin_export_full"
    ADMIN_ARCHIVE = "admin_archive"
    ADMIN_LOGOUT = "admin_logout"
    ADMIN_CHANGE_DATE = "admin_change_date"
    ADMIN_ARCHIVE_DOWNLOAD = "archive_download"
    ADMIN_ADD_NEXT = "admin_add_next"
    ADMIN_BACK = "admin_back"
    CONFIRM = "confirm"
    EDIT = "edit"
    MY_QR = "my_qr"
    REREGISTER = "reregister"
    MAIN_MENU = "main_menu"
    BIRTH_DATE_YES = "Да"
    BIRTH_DATE_NO = "Нет"
    CANCEL = "cancel"
    CANCEL_ADMIN = "cancel_admin"
    PROCESS_INFO = "process_info"
    ABOUT_BOT = "about_bot"
    BACK_TO_MAIN = "back_to_main"


# Разделитель для составных callback
CALLBACK_SEPARATOR = "|"

# Категории и интересы
CATEGORIES = [
    ("Абитуриент", "applicant"),
    ("Родитель", "parent"),
    ("Слушатель", "listener")
]

EDUCATION_INTERESTS = [
    ("Бакалавр", "bachelor"),
    ("Магистратура", "master"),
    ("Специалитет", "specialist"),
    ("Кадетский корпус", "cadet")
]

# Импортируем утилиты из нового модуля для обратной совместимости
from app.utils.helpers import (
    format_date_for_display,
    get_category_display,
    get_education_display,
    validate_email,
    build_menu_keyboard,
    build_callback_data,
    parse_callback_data
)