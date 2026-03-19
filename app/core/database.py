import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()

class Config:
    LOCAL_DB_HOST = os.getenv('LOCAL_DB_HOST')
    LOCAL_DB_PORT = os.getenv('LOCAL_DB_PORT')
    LOCAL_DB_NAME = os.getenv('LOCAL_DB_NAME')
    LOCAL_DB_USER = os.getenv('LOCAL_DB_USER')
    LOCAL_DB_PASSWORD = os.getenv('LOCAL_DB_PASSWORD')

def get_engine():
    # Создаём объект URL с автоматическим кодированием специальных символов
    url_object = URL.create(
        drivername="postgresql",
        username=Config.LOCAL_DB_USER,
        password=Config.LOCAL_DB_PASSWORD,
        host=Config.LOCAL_DB_HOST,
        port=Config.LOCAL_DB_PORT,
        database=Config.LOCAL_DB_NAME
    )
    return create_engine(url_object, echo=False, pool_size=5, max_overflow=10)

engine = get_engine()
SessionLocal = scoped_session(sessionmaker(bind=engine))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()