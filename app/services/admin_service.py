import os
import psutil
import logging
from datetime import datetime
from app.repositories.event import EventRepository
from app.repositories.registration import RegistrationRepository
from app.repositories.scan import ScanRepository
from app.core.config import Config

logger = logging.getLogger(__name__)

def get_statistics(db, event_id: int) -> dict:
    """
    Возвращает статистику по мероприятию (только активные регистрации).
    """
    reg_repo = RegistrationRepository(db)
    scan_repo = ScanRepository(db)
    event_repo = EventRepository(db)

    event = event_repo.get_by_id(event_id)
    if not event:
        return {}

    # Все регистрации (для общего количества)
    total = reg_repo.get_all_by_event(event_id)
    total_count = len(total)

    # Активные регистрации
    active_regs = [r for r in total if r.is_active]
    active_count = len(active_regs)

    admitted = 0
    denied = 0
    pending = 0

    for reg in active_regs:
        last_scan = scan_repo.get_last_by_registration(reg.id)
        if last_scan:
            if last_scan.status == 'admitted':
                admitted += 1
            elif last_scan.status == 'denied':
                denied += 1
            else:
                pending += 1
        else:
            pending += 1

    # Распределение по категориям (только активные)
    by_category = {}
    for reg in active_regs:
        cat = reg.category
        if cat:
            by_category[cat] = by_category.get(cat, 0) + 1
        else:
            by_category['не указано'] = by_category.get('не указано', 0) + 1

    # Распределение по интересам (только активные)
    by_education = {}
    for reg in active_regs:
        edu = reg.education_interest
        if edu:
            by_education[edu] = by_education.get(edu, 0) + 1
        else:
            by_education['не указано'] = by_education.get('не указано', 0) + 1

    return {
        'total_registrations': total_count,
        'active_registrations': active_count,
        'scans_admitted': admitted,
        'scans_denied': denied,
        'scans_pending': pending,
        'by_category': by_category,
        'by_education': by_education
    }

def get_archived_events(db):
    event_repo = EventRepository(db)
    return event_repo.get_archived()

def get_server_status() -> dict:
    status = {}
    logger.info("Calculating server status...")

    status['cpu_percent'] = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    status['memory_percent'] = mem.percent

    disk_root = psutil.disk_usage('/')
    status['disk_percent_root'] = disk_root.percent

    try:
        disk_mnt = psutil.disk_usage('/mnt')
        status['disk_percent_mnt'] = disk_mnt.percent
    except FileNotFoundError:
        status['disk_percent_mnt'] = 0

    backup_dir = Config.BACKUP_DIR
    logger.info(f"Backup directory: {backup_dir}")
    if os.path.exists(backup_dir):
        logger.info(f"Backup dir exists, contents: {os.listdir(backup_dir)}")
        backups = [f for f in os.listdir(backup_dir) if f.endswith('.sql.gz') or f.endswith('.tar.gz')]
        logger.info(f"Filtered backup files: {backups}")
        if backups:
            backups.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
            last_backup = backups[0]
            last_backup_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(backup_dir, last_backup)))
            status['last_backup'] = last_backup_time.strftime('%d.%m.%Y %H:%M')
            total_size = sum(os.path.getsize(os.path.join(backup_dir, f)) for f in backups)
            if total_size < 1024 * 1024:
                status['backup_size'] = f"{round(total_size / 1024, 2)} KB"
            else:
                status['backup_size'] = f"{round(total_size / (1024**2), 2)} MB"
        else:
            status['last_backup'] = "Нет бекапов"
            status['backup_size'] = "0 KB"
    else:
        status['last_backup'] = "Папка не найдена"
        status['backup_size'] = "0 KB"

    return status