#!/usr/bin/env python3
import os
import bcrypt
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
from dotenv import load_dotenv
from app.models import Event, Setting

load_dotenv()

def seed():
    # Читаем параметры из .env
    db_host = os.getenv('LOCAL_DB_HOST')
    db_port = os.getenv('LOCAL_DB_PORT')
    db_name = os.getenv('LOCAL_DB_NAME')
    db_user = os.getenv('LOCAL_DB_USER')
    db_password = os.getenv('LOCAL_DB_PASSWORD')
    
    # Формируем URL подключения
    url_object = URL.create(
        drivername="postgresql",
        username=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )
    
    engine = create_engine(url_object)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Проверим, есть ли уже мероприятия
    if session.query(Event).count() == 0:
        # Создаем первое мероприятие (замените дату на актуальную)
        event = Event(
            event_date=date(2026, 4, 15),
            description="День открытых дверей (весна 2026)",
            is_active=True,
            is_archived=False
        )
        session.add(event)
        session.flush()  # чтобы получить id

        # Устанавливаем текущее мероприятие в настройках
        current_event = Setting(
            key='current_event_id',
            value=str(event.id),
            description='ID активного мероприятия'
        )
        session.add(current_event)
        print(f"Создано мероприятие на {event.event_date} с ID {event.id}")
    else:
        print("Мероприятия уже существуют, пропускаем создание.")

    # Проверим, есть ли уже пароль администратора
    if session.query(Setting).filter_by(key='admin_password_hash').count() == 0:
        # Создаем хеш для пароля администратора (замените 'admin123' на реальный пароль)
        admin_password = 'admin123'  # ВРЕМЕННО, потом измените!
        hashed = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin_setting = Setting(
            key='admin_password_hash',
            value=hashed,
            description='Хеш пароля администратора'
        )
        session.add(admin_setting)
        print("Хеш пароля администратора создан.")
    else:
        print("Пароль администратора уже существует.")

    session.commit()
    print("Начальные данные успешно загружены.")

if __name__ == "__main__":
    seed()