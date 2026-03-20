from flask import Blueprint, request, render_template, redirect, url_for, make_response
from app.core.database import get_db
from app.services import scan_service, auth_service
from app.handlers.common import get_category_display, get_education_display
from app.repositories.registration import RegistrationRepository
from app.models import Scan
from app.core.config import Config
import uuid
import logging
from datetime import timedelta, datetime

webhook_bp = Blueprint('webhook', __name__)
qr_scan_bp = Blueprint('qr_scan', __name__)

def is_guard_authenticated(request):
    guard_cookie = request.cookies.get('guard_auth')
    return guard_cookie == 'yes'

@webhook_bp.route('', methods=['POST'])
def webhook():
    data = request.json
    logging.debug(f"Webhook received: {data}")
    try:
        from app.handlers.message_handler import handle_update
        handle_update(data)
    except Exception as e:
        logging.error(f"Error in webhook handler: {e}", exc_info=True)
        return f"Error: {str(e)}", 500
    return 'OK', 200

@qr_scan_bp.route('', methods=['GET', 'POST'])
def qr_scan():
    uid = request.args.get('uid') or request.form.get('uid')
    auth_mode = request.args.get('auth') == '1'
    logout = request.args.get('logout') == '1'

    # Выход (удаление cookie)
    if logout:
        # Получаем uid из параметров запроса (может быть в GET или POST)
        uid = request.args.get('uid') or request.form.get('uid')
        # Перенаправляем на ту же страницу с тем же uid (или без, если uid не было)
        redirect_url = url_for('qr_scan.qr_scan', uid=uid) if uid else url_for('qr_scan.qr_scan')
        resp = make_response(redirect(redirect_url))
        resp.delete_cookie('guard_auth')
        return resp

    # Обработка POST-запроса с паролем
    if request.method == 'POST' and request.form.get('password'):
        password = request.form.get('password')
        if auth_service.verify_guard_password(password):
            # Устанавливаем cookie на 24 часа
            resp = make_response(redirect(url_for('qr_scan.qr_scan', uid=uid)))
            expires = datetime.now() + timedelta(days=1)
            resp.set_cookie('guard_auth', 'yes', expires=expires, httponly=True, secure=Config.SECURE_COOKIE, samesite='Lax')
            return resp
        else:
            return render_template('scan_page.html', uid=uid, auth_error="Неверный пароль", auth_mode=True)

    # POST-запрос с изменением статуса (только для авторизованных)
    if request.method == 'POST' and request.form.get('status'):
        if not is_guard_authenticated(request):
            return redirect(url_for('qr_scan.qr_scan', uid=uid, auth=1))

        status = request.form.get('status')
        if not uid or not status:
            return render_template('scan_page.html', error="Не указаны UID или статус")

        db = next(get_db())
        try:
            reg_uuid = uuid.UUID(uid)
            reg_repo = RegistrationRepository(db)
            registration = reg_repo.get_by_uuid(reg_uuid)
            if not registration:
                return render_template('scan_page.html', error="Регистрация не найдена")

            scan_service.record_scan(db, reg_uuid, status)
            return redirect(url_for('qr_scan.qr_scan', uid=uid))
        finally:
            db.close()

    # GET-запрос или POST без пароля/статуса
    if not uid:
        return render_template('scan_page.html', error="UID не указан")

    db = next(get_db())
    try:
        reg_uuid = uuid.UUID(uid)
        reg_repo = RegistrationRepository(db)
        registration = reg_repo.get_by_uuid(reg_uuid)
        if not registration:
            return render_template('scan_page.html', error="QR-код не действителен или регистрация не найдена")

        if not registration.is_active:
            return render_template('scan_page.html', error="Эта регистрация уже не активна")

        last_scan = db.query(Scan).filter(
            Scan.registration_id == reg_uuid
        ).order_by(Scan.id.desc()).first()

        if last_scan:
            last_scan_status = last_scan.status
            last_scan_time = last_scan.scan_time + timedelta(seconds=Config.TIME_OFFSET)
        else:
            last_scan_status = None
            last_scan_time = None

        logging.info(f"Found scans for uid {uid}, last status: {last_scan_status}")

        is_guard = is_guard_authenticated(request)
        category_display = get_category_display(registration.category)
        education_display = get_education_display(registration.education_interest)

        return render_template(
            'scan_page.html',
            registration=registration,
            category_display=category_display,
            education_display=education_display,
            last_scan_status=last_scan_status,
            last_scan_time=last_scan_time,
            is_guard=is_guard,
            uid=uid,
            auth_mode=auth_mode,
            auth_error=None
        )
    finally:
        db.close()