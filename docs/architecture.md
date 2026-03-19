# Архитектура чат-бота @pass_agz_bot (регистрация на День открытых дверей)

## 1. Общее описание
Бот предназначен для регистрации посетителей на мероприятия (Дни открытых дверей). Пользователь проходит опрос, получает QR-код со ссылкой на страницу проверки. На входе сотрудник сканирует QR, видит данные и фиксирует пропуск/отказ. Администраторы имеют доступ к статистике, управлению датами и выгрузке Excel.

## 2. Технологический стек
- **Язык:** Python 3.10+
- **Веб-фреймворк:** Flask + Gunicorn
- **База данных:** PostgreSQL (локальная) с SQLAlchemy ORM
- **Генерация QR:** библиотека qrcode
- **Работа с Excel:** openpyxl
- **HTTP-клиент:** requests (для MAX API)
- **Веб-сервер:** Nginx (reverse proxy)
- **Менеджер процессов:** systemd
- **Платформа:** мессенджер MAX (вебхуки)

## 3. Компоненты системы
### 3.1. Flask-приложение
- **Эндпоинт /webhook** — принимает обновления от MAX.
- **Эндпоинт /qr-scan** — отображает данные по QR и принимает решение о пропуске.

### 3.2. Модели данных (SQLAlchemy)
- **Event** — мероприятия.
- **Registration** — регистрации пользователей.
- **Scan** — результаты сканирования.
- **AnonymizedStat** — обезличенная статистика прошедших мероприятий.
- **Setting** — настройки (пароль админа, текущее событие).
- **DialogState** — состояния диалогов пользователей.

### 3.3. Сервисы (бизнес-логика)
- `max_api.py` — отправка сообщений, фото, файлов в MAX.
- `auth_service.py` — проверка пароля администратора.
- `user_service.py` — работа с регистрациями и состояниями.
- `qr_service.py` — генерация QR-кодов.
- `scan_service.py` — запись сканирований.
- `anonymize_service.py` — анонимизация прошедших мероприятий.
- `export_service.py` — генерация Excel-файлов (полных и обезличенных).
- `admin_service.py` — статистика, управление мероприятиями, статус сервера.

### 3.4. Хендлеры (обработчики диалогов)
- `common.py` — константы, клавиатуры.
- `message_handler.py` — диспетчер входящих сообщений.
- `register.py` — сценарий регистрации.
- `admin.py` — вход в админку и команды администратора.

### 3.5. Шаблоны
- `templates/scan_page.html` — страница сканирования.

### 3.6. Вспомогательные скрипты
- `scripts/rotate_event.py` — ежедневная анонимизация и ротация мероприятий.
- `scripts/backup.sh` — резервное копирование БД и .env.

## 4. Схема базы данных
```sql
-- Таблица мероприятий
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Таблица регистраций
CREATE TABLE registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    birth_date DATE NOT NULL,
    birth_place TEXT NOT NULL,
    residence TEXT,
    email TEXT,
    category VARCHAR(20),  -- 'applicant', 'parent', 'listener'
    education_interest VARCHAR(20),  -- 'bachelor', 'master', 'specialist', 'cadet'
    registered_at TIMESTAMP DEFAULT NOW(),
    last_qr_sent_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Таблица сканирований
CREATE TABLE scans (
    id SERIAL PRIMARY KEY,
    registration_id UUID REFERENCES registrations(id) ON DELETE CASCADE,
    scan_time TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) NOT NULL,  -- 'admitted', 'denied', 'pending'
    scanned_by TEXT,
    comment TEXT
);

-- Таблица обезличенной статистики
CREATE TABLE anonymized_stats (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    birth_year INTEGER,
    birth_place TEXT,
    residence TEXT,
    category VARCHAR(20),
    education_interest VARCHAR(20),
    scan_status VARCHAR(20),  -- последний статус сканирования
    registered_at TIMESTAMP
);

-- Таблица настроек
CREATE TABLE settings (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Таблица состояний диалогов
CREATE TABLE dialog_states (
    user_id VARCHAR(255) PRIMARY KEY,
    state INTEGER NOT NULL,
    data JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);```