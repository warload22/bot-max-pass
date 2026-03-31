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
    """Сохраняет ФИО и переходит к вопросу о гражданстве."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['full_name'] = text.strip()
        dialog_repo.set(user_id, States.AWAITING_CITIZENSHIP, data)
        buttons = [
            ("✅ Да", CallbackActions.CITIZENSHIP_YES),
            ("❌ Нет", CallbackActions.CITIZENSHIP_NO),
            ("🚫 Отмена", CallbackActions.CANCEL)
        ]
        keyboard = build_menu_keyboard(buttons)
        max_api.send_message(chat_id, "Являетесь ли вы гражданином Российской Федерации?", keyboard=keyboard)
    finally:
        db.close()

def handle_citizenship(chat_id: int, user_id: int, callback_data: str) -> None:
    """Обрабатывает ответ о гражданстве."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        if callback_data == CallbackActions.CITIZENSHIP_YES:
            data['is_russian_citizen'] = True
            dialog_repo.set(user_id, States.AWAITING_BIRTH_YEAR, data)
            keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL)])
            max_api.send_message(chat_id, "Введите год вашего рождения (четыре цифры, например 1990):", keyboard=keyboard)
        else:
            # Не гражданин – регистрация отклонена
            data['is_russian_citizen'] = False
            dialog_repo.clear(user_id)
            max_api.send_message(
                chat_id,
                "На основании руководящих документов МЧС РФ допуск на режимный объект осуществляется только гражданам РФ.\n"
                "К сожалению, вы не можете пройти регистрацию."
            )
            from app.handlers.message_handler import send_main_menu
            send_main_menu(chat_id, user_id)
    finally:
        db.close()

def handle_birth_year(chat_id: int, user_id: int, text: str) -> None:
    """Проверяет и сохраняет год рождения."""
    if not re.match(r'^\d{4}$', text.strip()):
        max_api.send_message(chat_id, "Неверный формат. Введите год четырьмя цифрами (например, 1990):")
        return
    year = int(text.strip())
    current_year = datetime.now().year
    if year < 1900 or year > current_year:
        max_api.send_message(chat_id, f"Год должен быть от 1900 до {current_year}. Попробуйте ещё раз:")
        return

    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['birth_year'] = year
        dialog_repo.set(user_id, States.AWAITING_BIRTH_PLACE, data)
        keyboard = build_menu_keyboard([("❌ Отмена", CallbackActions.CANCEL)])
        max_api.send_message(chat_id, "Введите ваше место рождения (как в паспорте):", keyboard=keyboard)
    finally:
        db.close()

def handle_birth_place(chat_id: int, user_id: int, text: str) -> None:
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
        buttons = [(cat[0], cat[1]) for cat in CATEGORIES]
        buttons.append(("🚫 Отмена", CallbackActions.CANCEL))
        keyboard = build_menu_keyboard(buttons)
        max_api.send_message(chat_id, "Кто вы?", keyboard=keyboard)
    finally:
        db.close()

def handle_category(chat_id: int, user_id: int, callback_data: str) -> None:
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
        elif callback_data == 'listener':
            data['education_interest'] = None
            dialog_repo.set(user_id, States.CONFIRM_DATA, data)
            show_confirmation(chat_id, user_id, data)
        else:
            dialog_repo.set(user_id, States.AWAITING_EDUCATION_INTEREST, data)
            buttons = [(edu[0], edu[1]) for edu in EDUCATION_INTERESTS]
            buttons.append(("🚫 Отмена", CallbackActions.CANCEL))
            keyboard = build_menu_keyboard(buttons)
            max_api.send_message(chat_id, "Какое образование вас интересует?", keyboard=keyboard)
    finally:
        db.close()

def handle_school(chat_id: int, user_id: int, text: str) -> None:
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
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        if data is None:
            data = {}
        data['education_interest'] = callback_data
        dialog_repo.set(user_id, States.CONFIRM_DATA, data)
        show_confirmation(chat_id, user_id, data)
    finally:
        db.close()

def show_confirmation(chat_id: int, user_id: int, data: dict) -> None:
    """Показывает сводку введённых данных для подтверждения."""
    if not data or 'birth_year' not in data:
        logger.error("No data or birth_year in show_confirmation")
        return

    category_display = get_category_display(data['category'])
    education_display = get_education_display(data.get('education_interest')) if data.get('education_interest') else 'не указано'

    summary = (
        f"Проверьте введённые данные:\n\n"
        f"ФИО: {data['full_name']}\n"
        f"Гражданин РФ: {'Да' if data['is_russian_citizen'] else 'Нет'}\n"
        f"Год рождения: {data['birth_year']}\n"
        f"Место рождения: {data['birth_place']}\n"
        f"Место жительства: {data.get('residence', '')}\n"
        f"Email: {data['email']}\n"
        f"Категория: {category_display}\n"
    )
    if data.get('school'):
        summary += f"Учебное заведение: {data['school']}\n"
    summary += f"Интересующее образование: {education_display}\n\n"
    summary += "Всё верно?"
    summary += "\n\nНажимая «Подтвердить», вы даёте согласие на обработку персональных данных."

    buttons = [
        ("✅ Подтвердить", CallbackActions.CONFIRM),
        ("✏️ Изменить", CallbackActions.EDIT),
        ("🚫 Отмена", CallbackActions.CANCEL)
    ]
    keyboard = build_menu_keyboard(buttons)
    max_api.send_message(chat_id, summary, keyboard=keyboard)

def handle_confirm(chat_id: int, user_id: int) -> None:
    """Подтверждение данных: создание регистрации, генерация QR."""
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        event_repo = EventRepository(db)
        reg_repo = RegistrationRepository(db)

        state, data = dialog_repo.get(user_id)
        if not data or 'birth_year' not in data:
            max_api.send_message(chat_id, "Ошибка: данные не найдены. Начните заново.")
            dialog_repo.clear(user_id)
            return

        event = event_repo.get_current()
        if not event:
            max_api.send_message(chat_id, "Извините, в данный момент нет активных мероприятий.")
            dialog_repo.clear(user_id)
            return

        reg_repo.deactivate_old_by_email(data['email'], event.id)

        reg = reg_repo.create(
            event_id=event.id,
            full_name=data['full_name'],
            birth_year=data['birth_year'],
            birth_place=data['birth_place'],
            residence=data.get('residence', ''),
            email=data['email'],
            category=data['category'],
            education_interest=data.get('education_interest'),
            school=data.get('school'),
            is_russian_citizen=data['is_russian_citizen']
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
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        dialog_repo.clear(user_id)
        from app.handlers.message_handler import send_main_menu
        send_main_menu(chat_id, user_id)
    finally:
        db.close()

def handle_edit(chat_id: int, user_id: int) -> None:
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        dialog_repo.clear(user_id)
        handle_register_start(chat_id, user_id)
    finally:
        db.close()