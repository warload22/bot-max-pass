#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.anonymize_service import anonymize_past_events
from app.core.database import SessionLocal
from app.models import Event
from datetime import date

if __name__ == "__main__":
    # Проверка текущих событий
    db = SessionLocal()
    events = db.query(Event).all()
    print("Мероприятия в БД:")
    for e in events:
        print(f"  id={e.id}, date={e.event_date}, is_active={e.is_active}, is_archived={e.is_archived}")
    db.close()

    print("\nЗапуск анонимизации...")
    anonymize_past_events()
    print("Готово.")

    db = SessionLocal()
    events = db.query(Event).all()
    print("\nМероприятия после анонимизации:")
    for e in events:
        print(f"  id={e.id}, date={e.event_date}, is_active={e.is_active}, is_archived={e.is_archived}")
    db.close()
