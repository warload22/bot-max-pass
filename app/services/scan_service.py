import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Scan, Registration
import logging

def record_scan(db: Session, registration_id: uuid.UUID, status: str, scanned_by: str = None, comment: str = None) -> Scan:
    # Текущее время в UTC
    now = datetime.utcnow()
    logging.info(f"[record_scan] Setting scan time to {now} (UTC)")
    
    scan = Scan(
        registration_id=registration_id,
        status=status,
        scanned_by=scanned_by,
        comment=comment,
        scan_time=now  # явно передаём время
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    logging.info(f"[record_scan] Scan recorded: reg={registration_id}, status={status}, scan_id={scan.id}, scan_time={scan.scan_time}")
    return scan

def get_last_scan_status(db: Session, registration_id: uuid.UUID) -> str:
    scan = db.query(Scan).filter(
        Scan.registration_id == registration_id
    ).order_by(Scan.id.desc()).first()
    return scan.status if scan else None

def count_scans_by_status(db: Session, event_id: int) -> dict:
    from sqlalchemy import func
    from app.models import Registration

    result = db.query(
        Scan.status,
        func.count(Scan.id)
    ).join(
        Registration, Scan.registration_id == Registration.id
    ).filter(
        Registration.event_id == event_id
    ).group_by(Scan.status).all()

    stats = {status: count for status, count in result}
    return stats