#!/bin/bash
# Скрипт резервного копирования базы данных max_bot_pass_db
# Использует .pgpass для аутентификации

BACKUP_DIR="/opt/max_bot_pass/backups"
DB_NAME="max_bot_pass_db"
DB_USER="max_bot_user"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Дамп базы данных (пароль берётся из ~/.pgpass)
pg_dump -U "$DB_USER" -h localhost "$DB_NAME" | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Удаление старых бекапов (старше 7 дней)
find "$BACKUP_DIR" -name "db_*.sql.gz" -type f -mtime +7 -delete