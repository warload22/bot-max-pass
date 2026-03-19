import logging
import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.database import SessionLocal
from app.handlers.common import (
    States, CallbackActions, build_menu_keyboard,
    CATEGORIES, EDUCATION_INTERESTS,
    format_date_for_display, get_category_display, get_education_display,
    validate_email
)
from app.services import qr_service, max_api
from app.repositories.registration import RegistrationRepository
from app.repositories.event import EventRepository
from app.repositories.dialog_state import DialogStateRepository
from app.repositories.scan import ScanRepository

logger = logging.getLogger(__name__)

def handle_register_start(chat_id: int, user_id: int) -> None:
    """Начало регистрации: запрос ФИО."""
    logger.info(f"handle_register_start called for user {user_id}")
    db = SessionLocal()
    try:
        event_repo = EventRepository(db)
        dialog_repo = DialogStateRepository(db)
        event = event_repo.get_current()
        date_str = event.event_date.strftime('%d.%m.%Y') if event else "не определена"
        dialog_repo.set(user_id, States.AWAITING_FULL_NAME, {})
        keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL)])
        max_api.send_message(
            chat_id,
            f"Вы регистрируетесь на мероприятие {date_str}. Введите ваше полное имя (Фамилия Имя Отчество):",
            keyboard=keyboard
        )
    finally:
        db.close()

def handle_full_name(chat_id: int, user_id: int, text: str) -> None:
    """Сохраняет ФИО и переходит к дате рождения."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['full_name'] = text.strip()
        dialog_repo.set(user_id, States.AWAITING_BIRTH_DATE, data)
        keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL)])
        max_api.send_message(
            chat_id,
            "Введите вашу дату рождения в формате ДД.ММ.ГГГГ (например, 15.04.1999):",
            keyboard=keyboard
        )
    finally:
        db.close()

def handle_birth_date(chat_id: int, user_id: int, text: str) -> None:
    """Проверяет дату, сохраняет и запрашивает подтверждение."""
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', text.strip()):
        max_api.send_message(chat_id, "Неверный формат. Введите дату в формате ДД.ММ.ГГГГ:")
        return

    try:
        date_obj = datetime.strptime(text.strip(), "%d.%m.%Y").date()
    except ValueError:
        max_api.send_message(chat_id, "Такой даты не существует. Проверьте ввод и повторите:")
        return

    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['birth_date'] = date_obj.isoformat()
        data['awaiting_confirmation'] = True
        dialog_repo.set(user_id, States.AWAITING_BIRTH_DATE, data)

        formatted = format_date_for_display(date_obj)
        buttons = [
            ("✅ Да", CallbackActions.BIRTH_DATE_YES),
            ("❌ Нет", CallbackActions.BIRTH_DATE_NO),
            ("🚫 Отмена", CallbackActions.CANCEL)
        ]
        keyboard = build_menu_keyboard(buttons)
        max_api.send_message(
            chat_id,
            f"Вы ввели {formatted}. Всё верно?",
            keyboard=keyboard
        )
    finally:
        db.close()

def handle_birth_date_confirmation(chat_id: int, user_id: int, callback_data: str) -> None:
    """Обрабатывает подтверждение даты (Да/Нет)."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        if callback_data == CallbackActions.BIRTH_DATE_YES:
            dialog_repo.set(user_id, States.AWAITING_BIRTH_PLACE, data)
            keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL)])
            max_api.send_message(chat_id, "Введите ваше место рождения (как в паспорте):", keyboard=keyboard)
        else:  # Нет
            data.pop('birth_date', None)
            data.pop('awaiting_confirmation', None)
            dialog_repo.set(user_id, States.AWAITING_BIRTH_DATE, data)
            keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL)])
            max_api.send_message(chat_id, "Введите дату рождения ещё раз (в формате ДД.ММ.ГГГГ):", keyboard=keyboard)
    finally:
        db.close()

def handle_birth_place(chat_id: int, user_id: int, text: str) -> None:
    """Сохраняет место рождения, переходит к месту жительства."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['birth_place'] = text.strip()
        dialog_repo.set(user_id, States.AWAITING_RESIDENCE, data)
        keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL)])
        max_api.send_message(chat_id, "Введите ваше место жительства (город/регион):", keyboard=keyboard)
    finally:
        db.close()

def handle_residence(chat_id: int, user_id: int, text: str) -> None:
    """Сохраняет место жительства, переходит к email."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['residence'] = text.strip()
        dialog_repo.set(user_id, States.AWAITING_EMAIL, data)
        keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL)])
        max_api.send_message(chat_id, "Введите ваш email:", keyboard=keyboard)
    finally:
        db.close()

def handle_email(chat_id: int, user_id: int, text: str) -> None:
    """Проверяет email, сохраняет и переходит к выбору категории."""
    email = text.strip().lower()
    if not validate_email(email):
        max_api.send_message(chat_id, "Неверный формат email. Попробуйте ещё раз:")
        return
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['email'] = email
        dialog_repo.set(user_id, States.AWAITING_CATEGORY, data)
        # Кнопки категорий + отмена
        buttons = [(cat[0], cat[1]) for cat in CATEGORIES]
        buttons.append(("🚫 Отмена", CallbackActions.CANCEL))
        keyboard = build_menu_keyboard(buttons)
        max_api.send_message(chat_id, "Кто вы?", keyboard=keyboard)
    finally:
        db.close()

def handle_category(chat_id: int, user_id: int, callback_data: str) -> None:
    """Обработка выбора категории. Для абитуриентов запрашиваем учебное заведение."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['category'] = callback_data
        dialog_repo.set(user_id, States.AWAITING_CATEGORY, data)

        if callback_data == 'applicant':
            dialog_repo.set(user_id, States.AWAITING_SCHOOL, data)
            keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL)])
            max_api.send_message(chat_id, "Из какого вы учебного заведения? (введите название школы/колледжа/вуза)", keyboard=keyboard)
        else:
            dialog_repo.set(user_id, States.AWAITING_EDUCATION_INTEREST, data)
            buttons = [(edu[0], edu[1]) for edu in EDUCATION_INTERESTS]
            buttons.append(("🚫 Отмена", CallbackActions.CANCEL))
            keyboard = build_menu_keyboard(buttons)
            max_api.send_message(chat_id, "Какое образование вас интересует?", keyboard=keyboard)
    finally:
        db.close()

def handle_school(chat_id: int, user_id: int, text: str) -> None:
    """Сохраняет учебное заведение и переходит к выбору образования."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['school'] = text.strip()
        dialog_repo.set(user_id, States.AWAITING_EDUCATION_INTEREST, data)
        buttons = [(edu[0], edu[1]) for edu in EDUCATION_INTERESTS]
        buttons.append(("🚫 Отмена", CallbackActions.CANCEL))
        keyboard = build_menu_keyboard(buttons)
        max_api.send_message(chat_id, "Какое образование вас интересует?", keyboard=keyboard)
    finally:
        db.close()

def handle_education_interest(chat_id: int, user_id: int, callback_data: str) -> None:
    """Сохраняет интерес, показывает сводку данных для подтверждения."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['education_interest'] = callback_data
        dialog_repo.set(user_id, States.CONFIRM_DATA, data)
        logger.info(f"Data before confirmation: {data}")

        if not data or 'birth_date' not in data:
            dialog_repo.clear(user_id)
            max_api.send_message(chat_id, "Произошла ошибка. Начните регистрацию заново.")
            return

        birth_date_obj = datetime.fromisoformat(data['birth_date']).date()
        birth_date_str = format_date_for_display(birth_date_obj)
        category_display = get_category_display(data['category'])
        education_display = get_education_display(data['education_interest'])

        summary = (
            f"Проверьте введённые данные:\n\n"
            f"ФИО: {data['full_name']}\n"
            f"Дата рождения: {birth_date_str}\n"
            f"Место рождения: {data['birth_place']}\n"
            f"Место жительства: {data.get('residence', '')}\n"
            f"Email: {data['email']}\n"
            f"Категория: {category_display}\n"
        )
        if data.get('school'):
            summary += f"Учебное заведение: {data['school']}\n"
        summary += f"Интересующее образование: {education_display}\n\n"
        summary += "Всё верно?"

        buttons = [
            ("✅ Подтвердить", CallbackActions.CONFIRM),
            ("✏️ Изменить", CallbackActions.EDIT),
            ("🚫 Отмена", CallbackActions.CANCEL)
        ]
        keyboard = build_menu_keyboard(buttons)
        max_api.send_message(chat_id, summary, keyboard=keyboard)
    finally:
        db.close()

def handle_confirm(chat_id: int, user_id: int) -> None:
    """Подтверждение данных: создание регистрации, генерация QR, отправка."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        event_repo = EventRepository(db)
        reg_repo = RegistrationRepository(db)

        state, data = dialog_repo.get(user_id)
        if not data or 'birth_date' not in data:
            max_api.send_message(chat_id, "Ошибка: данные не найдены. Начните заново.")
            dialog_repo.clear(user_id)
            return

        event = event_repo.get_current()
        if not event:
            max_api.send_message(chat_id, "Извините, в данный момент нет активных мероприятий.")
            dialog_repo.clear(user_id)
            return

        # Деактивируем старые регистрации пользователя на это мероприятие
        reg_repo.deactivate_old_by_email(data['email'], event.id)

        birth_date = datetime.fromisoformat(data['birth_date']).date()
        reg = reg_repo.create(
            event_id=event.id,
            full_name=data['full_name'],
            birth_date=birth_date,
            birth_place=data['birth_place'],
            residence=data.get('residence', ''),
            email=data['email'],
            category=data['category'],
            education_interest=data['education_interest'],
            school=data.get('school')
        )

        qr_bytes = qr_service.generate_qr_for_registration(reg.id)
        caption = (
            "✅ Регистрация на День открытых дверей успешно завершена!\n\n"
            "Этот QR-код является вашим пропуском на территорию Академии. При входе на КПП предъявите данный QR-код сотруднику охраны вместе с паспортом для сверки данных. После проверки вас пропустят на мероприятие.\n\n"
            "Сохраните этот QR-код до даты проведения."
        )
        max_api.send_photo(chat_id, qr_bytes, caption=caption)

        main_menu_keyboard = build_menu_keyboard([
            ("📱 Мой QR", CallbackActions.MY_QR),
            ("🔄 Перерегистрироваться", CallbackActions.REREGISTER),
            ("🏠 Главное меню", CallbackActions.MAIN_MENU)
        ])
        max_api.send_message(
            chat_id,
            "Вы успешно зарегистрированы!\n\n"
            "Вы можете повторно отправить QR-код, перерегистрироваться (старый код станет недействительным) или вернуться в главное меню.",
            keyboard=main_menu_keyboard
        )
        dialog_repo.set(user_id, States.AFTER_REGISTRATION, {'reg_id': str(reg.id)})
    except Exception as e:
        logger.error(f"Error in handle_confirm: {e}", exc_info=True)
        max_api.send_message(chat_id, "Произошла ошибка при регистрации. Попробуйте позже.")
        dialog_repo.clear(user_id)
    finally:
        db.close()

def handle_my_qr(chat_id: int, user_id: int) -> None:
    """Повторная отправка QR-кода."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        reg_repo = RegistrationRepository(db)
        state, data = dialog_repo.get(user_id)
        if state != States.AFTER_REGISTRATION or not data or 'reg_id' not in data:
            max_api.send_message(chat_id, "Сначала зарегистрируйтесь.")
            return
        reg_uuid = uuid.UUID(data['reg_id'])
        reg = reg_repo.get_by_uuid(reg_uuid)
        if not reg:
            max_api.send_message(chat_id, "Регистрация не найдена.")
            return
        qr_bytes = qr_service.generate_qr_for_registration(reg.id)
        max_api.send_photo(chat_id, qr_bytes, "Ваш QR-код")
    finally:
        db.close()

def handle_reregister(chat_id: int, user_id: int) -> None:
    """Перерегистрация: деактивирует старую и начинает новую."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        reg_repo = RegistrationRepository(db)
        state, data = dialog_repo.get(user_id)
        if state == States.AFTER_REGISTRATION and data and 'reg_id' in data:
            reg_uuid = uuid.UUID(data['reg_id'])
            reg = reg_repo.get_by_uuid(reg_uuid)
            if reg:
                reg.is_active = False
                db.commit()
        dialog_repo.clear(user_id)
        handle_register_start(chat_id, user_id)
    finally:
        db.close()

def handle_main_menu(chat_id: int, user_id: int) -> None:
    """Возврат в главное меню."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        dialog_repo.clear(user_id)
        from app.handlers.message_handler import send_main_menu
        send_main_menu(chat_id, user_id)
    finally:
        db.close()

def handle_edit(chat_id: int, user_id: int) -> None:
    """Возврат к первому шагу регистрации (изменение данных)."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        dialog_repo.clear(user_id)
        handle_register_start(chat_id, user_id)
    finally:
        db.close()