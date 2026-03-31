import logging
from typing import Optional, Dict, Any

from pydantic import ValidationError

from app.core.database import SessionLocal
from app.services import max_api
from app.handlers.common import States, parse_callback_data, build_menu_keyboard, CallbackActions
from app.handlers import register
from app.handlers import admin
from app.schemas.webhook import WebhookUpdate
from app.repositories.dialog_state import DialogStateRepository

logger = logging.getLogger(__name__)

def handle_update(update_data: Dict[str, Any]) -> None:
    """Главный обработчик входящих обновлений от MAX с валидацией через Pydantic."""
    try:
        update = WebhookUpdate(**update_data)
    except ValidationError as e:
        logger.error(f"Invalid webhook data: {e}")
        return

    logger.debug(f"Received update_type: {update.update_type}")

    if update.update_type == 'message_created':
        if not update.message:
            logger.warning("Missing message in message_created")
            return
        chat_id = update.message.recipient.chat_id
        user_id = update.message.sender.user_id
        text = update.message.body.text or ''
        mid = update.message.body.mid

        if not chat_id or not user_id:
            logger.warning("Missing chat_id or user_id in message")
            return

        handle_message(chat_id, user_id, text, mid)

    elif update.update_type == 'bot_started':
        chat_id = update.chat_id
        user_id = update.user_id
        if chat_id and user_id:
            handle_start(chat_id, user_id)

    elif update.update_type == 'message_callback':
        if not update.callback:
            logger.warning("Missing callback in message_callback")
            return
        chat_id = update.message.recipient.chat_id if update.message else None
        user_id = update.callback.user.user_id
        callback_data = update.callback.payload

        if not chat_id or not user_id:
            logger.warning("Missing chat_id or user_id in callback")
            return

        handle_callback(chat_id, user_id, callback_data)
    else:
        logger.debug(f"Unhandled update_type: {update.update_type}")

def handle_message(chat_id, user_id, text, mid=None):
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)

        if state is None:
            if text == '/admin':
                admin.handle_admin_command(chat_id, user_id)
                return
            elif text == '/start':
                handle_start(chat_id, user_id)
                return
            else:
                send_main_menu(chat_id, user_id)
                return

        if state == States.AWAITING_FULL_NAME:
            register.handle_full_name(chat_id, user_id, text)
        elif state == States.AWAITING_CITIZENSHIP:
            # Ожидание callback'а, текст не обрабатываем
            max_api.send_message(chat_id, "Пожалуйста, выберите вариант с помощью кнопок.")
        elif state == States.AWAITING_BIRTH_YEAR:
            register.handle_birth_year(chat_id, user_id, text)
        elif state == States.AWAITING_BIRTH_PLACE:
            register.handle_birth_place(chat_id, user_id, text)
        elif state == States.AWAITING_RESIDENCE:
            register.handle_residence(chat_id, user_id, text)
        elif state == States.AWAITING_EMAIL:
            register.handle_email(chat_id, user_id, text)
        elif state == States.AWAITING_ADMIN_PASSWORD:
            admin.handle_admin_password(chat_id, user_id, text, mid)
        elif state == States.ADMIN_AWAITING_NEW_DATE:
            admin.handle_new_date_input(chat_id, user_id, text)
        elif state == States.ADMIN_AWAITING_NEXT_EVENT_DATE:
            admin.handle_next_event_date_input(chat_id, user_id, text)
        elif state == States.AWAITING_SCHOOL:
            register.handle_school(chat_id, user_id, text)
        else:
            dialog_repo.clear(user_id)
            send_main_menu(chat_id, user_id)
    finally:
        db.close()

def handle_callback(chat_id, user_id, callback_data):
    logging.info(f"handle_callback: chat_id={chat_id}, user_id={user_id}, callback_data={callback_data}")
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        state, data = dialog_repo.get(user_id)
        action, args = parse_callback_data(callback_data)
        logging.info(f"Parsed action={action}, args={args}")

        # Глобальная отмена регистрации (работает в любом состоянии)
        if action == CallbackActions.CANCEL:
            dialog_repo.clear(user_id)
            send_main_menu(chat_id, user_id)
            return

        # Возврат в главное меню из информационных разделов
        if action == CallbackActions.BACK_TO_MAIN:
            dialog_repo.clear(user_id)
            send_main_menu(chat_id, user_id)
            return

        # Если состояние - административное ожидание ввода даты,
        # направляем все callback'и в admin.handle_admin_callback
        if state in (States.ADMIN_AWAITING_NEW_DATE, States.ADMIN_AWAITING_NEXT_EVENT_DATE):
            admin.handle_admin_callback(chat_id, user_id, action, args)
            return

        if state is None:
            handle_main_menu_callback(chat_id, user_id, action)
            return

        if state == States.AWAITING_CITIZENSHIP:
            register.handle_citizenship(chat_id, user_id, action)
        elif state == States.AWAITING_CATEGORY:
            register.handle_category(chat_id, user_id, action)
        elif state == States.AWAITING_EDUCATION_INTEREST:
            register.handle_education_interest(chat_id, user_id, action)
        elif state == States.CONFIRM_DATA:
            if action == CallbackActions.CONFIRM:
                register.handle_confirm(chat_id, user_id)
            elif action == CallbackActions.EDIT:
                register.handle_edit(chat_id, user_id)
        elif state == States.ADMIN_MENU:
            admin.handle_admin_callback(chat_id, user_id, action, args)
        elif state == States.AFTER_REGISTRATION:
            if action == CallbackActions.MY_QR:
                register.handle_my_qr(chat_id, user_id)
            elif action == CallbackActions.REREGISTER:
                register.handle_reregister(chat_id, user_id)
            elif action == CallbackActions.MAIN_MENU:
                register.handle_main_menu(chat_id, user_id)
            else:
                logging.warning(f"Unhandled action in AFTER_REGISTRATION: {action}")
                max_api.send_message(chat_id, "Неизвестная команда.")
        else:
            logging.warning(f"Unhandled callback in state {state}: {action}")
            max_api.send_message(chat_id, "Неизвестная команда.")
    finally:
        db.close()

def handle_start(chat_id: int, user_id: int) -> None:
    """Обрабатывает событие bot_started (первый запуск)."""
    logger.info(f"handle_start called for user {user_id}")
    db = SessionLocal()
    try:
        dialog_repo = DialogStateRepository(db)
        dialog_repo.clear(user_id)
        send_main_menu(chat_id, user_id)
    finally:
        db.close()

def send_main_menu(chat_id: int, user_id: int) -> None:
    """Отправляет главное меню пользователю."""
    from app.repositories.event import EventRepository
    db = SessionLocal()
    try:
        event_repo = EventRepository(db)
        event = event_repo.get_current()
        date_str = event.event_date.strftime('%d.%m.%Y') if event else "не определена"
    finally:
        db.close()

    text = (
        f"Добро пожаловать в чат-бот для регистрации на День открытых дверей Академии!\n\n"
        f"Ближайшее мероприятие состоится {date_str}.\n\n"
        "Чтобы пройти на мероприятие, необходимо зарегистрироваться, получить QR-код и при входе предъявить его вместе с паспортом.\n\n"
        "Выберите действие:"
    )
    buttons = [
        ("📝 Зарегистрироваться", CallbackActions.REGISTER),
        ("ℹ️ Процесс регистрации", CallbackActions.PROCESS_INFO),
        ("📚 О боте", CallbackActions.ABOUT_BOT)
    ]
    keyboard = build_menu_keyboard(buttons, row_width=1)
    max_api.send_message(chat_id, text, keyboard=keyboard)

def send_process_info(chat_id: int, user_id: int) -> None:
    """Отправляет информацию о процессе регистрации."""
    text = (
        "📋 Процесс регистрации:\n\n"
        "1️⃣ Введите ваши данные (ФИО, дата рождения, место рождения, место жительства, email).\n"
        "2️⃣ Укажите, кем вы являетесь (абитуриент, родитель, слушатель) и какое образование вас интересует.\n"
        "3️⃣ Подтвердите введённые данные.\n"
        "4️⃣ Получите QR-код, который необходимо сохранить.\n"
        "5️⃣ В день мероприятия предъявите QR-код и паспорт на входе – это ваш пропуск на территорию Академии.\n\n"
        "После регистрации вы сможете повторно отправить QR-код или перерегистрироваться (старый код станет недействительным)."
    )
    keyboard = build_menu_keyboard([("🔙 Назад", CallbackActions.BACK_TO_MAIN)])
    max_api.send_message(chat_id, text, keyboard=keyboard)

def send_about_bot(chat_id: int, user_id: int) -> None:
    """Отправляет информацию о боте."""
    text = (
        "🤖 Чат-бот «День открытых дверей АГЗ МЧС России» разработан отделом (современных средств обучения) центра (учебно-методического) Академии гражданской защиты МЧС России.\n\n"
        "По всем вопросам и предложениям обращайтесь:\n"
        "📞 телефон: 8 (498) 699-04-05\n\n"
        "Мы всегда рады помочь!"
    )
    keyboard = build_menu_keyboard([("🔙 Назад", CallbackActions.BACK_TO_MAIN)])
    max_api.send_message(chat_id, text, keyboard=keyboard)

def handle_main_menu_callback(chat_id: int, user_id: int, action: str) -> None:
    """Обрабатывает callback'и из главного меню."""
    logger.info(f"handle_main_menu_callback: action={action}")
    if action == CallbackActions.REGISTER:
        register.handle_register_start(chat_id, user_id)
    elif action == CallbackActions.PROCESS_INFO:
        send_process_info(chat_id, user_id)
    elif action == CallbackActions.ABOUT_BOT:
        send_about_bot(chat_id, user_id)
    elif action == CallbackActions.MY_QR:
        register.handle_my_qr(chat_id, user_id)
    elif action == CallbackActions.REREGISTER:
        register.handle_reregister(chat_id, user_id)
    elif action == CallbackActions.MAIN_MENU:
        register.handle_main_menu(chat_id, user_id)
    else:
        max_api.send_message(chat_id, "Неизвестная команда.")