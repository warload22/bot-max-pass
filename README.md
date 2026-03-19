# Чат-бот для регистрации на День открытых дверей (MAX)

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Бот для мессенджера MAX, позволяющий посетителям зарегистрироваться на мероприятие, получить персональный QR-код, а сотрудникам — сканировать код и фиксировать проход. Система автоматически управляет датами мероприятий и анонимизирует данные после завершения.

## Возможности

- 📝 **Регистрация пользователей**: сбор ФИО, даты рождения, места рождения, email, категории (абитуриент, родитель, слушатель), интереса (бакалавр, магистратура и др.), для абитуриентов — учебное заведение.
- 🔲 **Генерация QR-кода**: создание уникального QR со ссылкой на страницу проверки.
- 🔄 **Управление регистрацией**: повторная отправка QR, перерегистрация (старый код деактивируется).
- 👨‍💼 **Административная панель** (по скрытой команде `/admin`):
  - статистика по текущему мероприятию (активные регистрации, пропущенные/непропущенные, распределение по категориям и интересам);
  - управление датами (изменение даты текущего мероприятия, создание следующего);
  - просмотр логов сервера;
  - информация о статусе сервера (CPU, RAM, диски, бекапы);
  - выгрузка полных данных (Excel) и обезличенной статистики.
- 🛡️ **Страница сканирования**:
  - любой пользователь может посмотреть статус своего QR;
  - сотрудники входят по паролю (cookie на 24 часа) и могут отмечать пропуск/отказ.
- ⏳ **Автоматическая анонимизация**: после даты мероприятия данные переносятся в обезличенную таблицу, а следующее мероприятие активируется.

## Технологический стек

- **Язык**: Python 3.10+
- **Веб-фреймворк**: Flask + Gunicorn
- **База данных**: PostgreSQL + SQLAlchemy (репозитории)
- **Валидация**: Pydantic
- **Работа с MAX API**: requests
- **Генерация QR**: qrcode[pil]
- **Excel**: openpyxl
- **Мониторинг**: psutil
- **Веб-сервер**: Nginx (reverse proxy)
- **Менеджер процессов**: systemd
- **Планировщик**: cron (анонимизация, бекапы)

## Установка и настройка

### Предварительные требования

- Сервер с Ubuntu 20.04/22.04
- PostgreSQL 12+
- Python 3.10+ и pip
- Nginx
- Доступ к интернету для установки пакетов

### Пошаговая инструкция

1. **Клонируйте репозиторий**

```
git clone https://github.com/your-username/bot-max-pass.git
cd bot-max-pass
```
Создайте виртуальное окружение и установите зависимости

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Настройте базу данных PostgreSQL

Создайте базу данных и пользователя.

Скопируйте .env.example в .env и отредактируйте параметры подключения:
```
cp .env.example .env
nano .env
```
Пример .env:

```
LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=5432
LOCAL_DB_NAME=your_db_name
LOCAL_DB_USER=your_db_user
LOCAL_DB_PASSWORD=your_db_password
MAX_BOT_TOKEN=your_token_from_max
APP_SECRET=your_random_secret_key
QR_BASE_URL=https://your-domain.com/qr-scan
TIME_OFFSET=10800   # для Москвы UTC+3
````

Инициализируйте базу данных

```
python init_db.py
```
Запустите бота через Gunicorn (для продакшена используйте systemd)
```
gunicorn --workers 3 --bind 127.0.0.1:5001 bot:create_app()
```
Настройте Nginx как reverse proxy (пример конфигурации):

```
location /webhook2 {
    proxy_pass http://127.0.0.1:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /qr-scan {
    proxy_pass http://127.0.0.1:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```
Настройте автозапуск через systemd (пример файла max_bot_pass.service см. в документации).

Настройте crontab для ежедневных задач:

```
0 3 * * * /opt/max_bot_pass/scripts/backup.sh >> /opt/max_bot_pass/logs/backup.log 2>&1
0 4 * * * cd /opt/max_bot_pass && /opt/max_bot_pass/venv/bin/python scripts/rotate_event.py >> /opt/max_bot_pass/logs/anonymize.log 2>&1
```

### Структура проекта (основное)

.
├── app/
│   ├── api/               # эндпоинты (webhook, qr-scan)
│   ├── core/              # конфигурация, подключение к БД
│   ├── handlers/           # логика обработки сообщений
│   │   ├── admin/          # модули административной панели
│   │   ├── common.py       # константы и общие функции
│   │   ├── message_handler.py
│   │   └── register.py
│   ├── models.py           # модели SQLAlchemy
│   ├── repositories/       # репозитории для работы с БД
│   ├── schemas/            # Pydantic схемы для вебхуков
│   ├── services/           # сервисы (MAX API, анонимизация, экспорт)
│   └── utils/              # вспомогательные функции
├── scripts/                # вспомогательные скрипты (backup, rotate_event)
├── templates/              # HTML-шаблон страницы сканирования
├── .env.example            # пример конфигурации
├── bot.py                  # точка входа Flask
├── init_db.py              # инициализация БД
└── requirements.txt        # зависимости

### Безопасность
Все секреты хранятся в файле .env (не включается в репозиторий).

Пароль для охранников хранится в БД в виде хеша (bcrypt).

Cookie аутентификации устанавливается с флагами HttpOnly, Secure (в production) и SameSite=Lax.

Для доступа к базе данных из скриптов рекомендуется использовать файл .pgpass.

### Тестирование
После установки рекомендуется проверить:

Регистрацию нового пользователя (все шаги).

Генерацию и повторную отправку QR-кода.

Вход в административную панель и работу всех функций (статистика, управление датами, логи, статус, выгрузка).

Страницу сканирования:

переход по ссылке с UUID без авторизации (видны только данные);

вход по паролю и появление кнопок;

изменение статуса и его сохранение.

Автоматическую анонимизацию (можно имитировать, изменив дату мероприятия).

### Лицензия
Этот проект распространяется под лицензией MIT. Подробнее см. в файле LICENSE.

Примечание: данный репозиторий содержит только код бота. Все секреты и реальные настройки необходимо хранить отдельно