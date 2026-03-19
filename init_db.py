#!/usr/bin/env python3
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv
from app.models import Base

load_dotenv()

def init_db():
    db_host = os.getenv('LOCAL_DB_HOST')
    db_port = os.getenv('LOCAL_DB_PORT')
    db_name = os.getenv('LOCAL_DB_NAME')
    db_user = os.getenv('LOCAL_DB_USER')
    db_password = os.getenv('LOCAL_DB_PASSWORD')
    
    # Создаём объект URL
    url_object = URL.create(
        drivername="postgresql",
        username=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )
    
    engine = create_engine(url_object, echo=True)
    Base.metadata.create_all(engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()