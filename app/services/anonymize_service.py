import logging
from datetime import date
from app.repositories.event import EventRepository
from app.repositories.registration import RegistrationRepository
from app.repositories.scan import ScanRepository
from app.repositories.anonymized_stat import AnonymizedStatRepository
from app.repositories.setting import SettingRepository
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

def anonymize_event(event_id: int) -> int:
    """Анонимизирует данные для указанного мероприятия."""
    db = SessionLocal()
    try:
        event_repo = EventRepository(db)
        reg_repo = RegistrationRepository(db)
        scan_repo = ScanRepository(db)
        anon_repo = AnonymizedStatRepository(db)

        event = event_repo.get_by_id(event_id)
        if not event:
            logger.error(f"Event {event_id} not found for anonymization.")
            return 0

        registrations = reg_repo.get_all_by_event(event_id)
        count = 0
        for reg in registrations:
            last_scan = scan_repo.get_last_by_registration(reg.id)
            scan_status = last_scan.status if last_scan else None

            anon_repo.create(
                event_id=event_id,
                birth_year=reg.birth_date.year,
                birth_place=reg.birth_place,
                residence=reg.residence,
                category=reg.category,
                education_interest=reg.education_interest,
                scan_status=scan_status,
                registered_at=reg.registered_at
            )
            count += 1

        # Сначала удаляем все сканы (они зависят от регистраций)
        for reg in registrations:
            # удаляем сканы (можно через репозиторий, но проще напрямую)
            db.query(Scan).filter(Scan.registration_id == reg.id).delete()

        # Теперь можно удалить регистрации
        db.query(Registration).filter(Registration.event_id == event_id).delete()

        event_repo.archive(event_id)
        db.commit()
        logger.info(f"Anonymized event {event_id}: {count} registrations processed.")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Error anonymizing event {event_id}: {e}")
        return 0
    finally:
        db.close()

def anonymize_past_events():
    """Находит все не архивированные прошедшие мероприятия и анонимизирует их."""
    db = SessionLocal()
    try:
        event_repo = EventRepository(db)
        setting_repo = SettingRepository(db)
        today = date.today()

        # Находим прошедшие неархивированные мероприятия
        past_events = db.query(Event).filter(
            Event.event_date < today,
            Event.is_archived == False
        ).all()

        for event in past_events:
            logger.info(f"Starting anonymization for event {event.id} ({event.event_date})")
            anonymize_event(event.id)

        # Активируем следующее мероприятие
        next_event = db.query(Event).filter(
            Event.event_date >= today,
            Event.is_archived == False,
            Event.is_active == False
        ).order_by(Event.event_date).first()

        if next_event:
            # Деактивируем текущее активное (если есть)
            current_active = db.query(Event).filter(Event.is_active == True).first()
            if current_active:
                current_active.is_active = False
            next_event.is_active = True

            setting_repo.set('current_event_id', str(next_event.id))
            logger.info(f"Activated next event {next_event.id} ({next_event.event_date})")
        else:
            logger.info("No future events to activate.")
    finally:
        db.close()