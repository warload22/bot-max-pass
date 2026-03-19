from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    event_date = Column(Date, nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default='now()')
    updated_at = Column(DateTime, server_default='now()', onupdate='now()')

    registrations = relationship('Registration', back_populates='event', cascade='all, delete-orphan')
    anonymized_stats = relationship('AnonymizedStat', back_populates='event', cascade='all, delete-orphan')

class Registration(Base):
    __tablename__ = 'registrations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    full_name = Column(String(255), nullable=False)
    birth_date = Column(Date, nullable=False)
    birth_place = Column(Text, nullable=False)
    residence = Column(Text)
    email = Column(String(255))
    category = Column(String(20))  # 'applicant', 'parent', 'listener'
    education_interest = Column(String(20))  # 'bachelor', 'master', 'specialist', 'cadet'
    school = Column(String(255))  # новое поле для учебного заведения (только для абитуриентов)
    registered_at = Column(DateTime, server_default='now()')
    last_qr_sent_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    event = relationship('Event', back_populates='registrations')
    scans = relationship('Scan', back_populates='registration', cascade='all, delete-orphan')

class Scan(Base):
    __tablename__ = 'scans'
    id = Column(Integer, primary_key=True)
    registration_id = Column(UUID(as_uuid=True), ForeignKey('registrations.id'), nullable=False)
    scan_time = Column(DateTime, server_default='now()')
    status = Column(String(20), nullable=False)  # 'admitted', 'denied', 'pending'
    scanned_by = Column(String(255))
    comment = Column(Text)

    registration = relationship('Registration', back_populates='scans')

class AnonymizedStat(Base):
    __tablename__ = 'anonymized_stats'
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    birth_year = Column(Integer)
    birth_place = Column(Text)
    residence = Column(Text)
    category = Column(String(20))
    education_interest = Column(String(20))
    scan_status = Column(String(20))  # последний статус сканирования
    school = Column(String(255))  # добавлено
    registered_at = Column(DateTime)

    event = relationship('Event', back_populates='anonymized_stats')

class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String(50), primary_key=True)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, server_default='now()', onupdate='now()')

class DialogState(Base):
    __tablename__ = 'dialog_states'
    user_id = Column(Integer, primary_key=True)
    state = Column(Integer, nullable=False)
    data = Column(JSON)
    updated_at = Column(DateTime, server_default='now()', onupdate='now()')