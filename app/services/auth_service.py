import bcrypt
import logging
from app.core.database import SessionLocal
from app.repositories.setting import SettingRepository

logger = logging.getLogger(__name__)

def verify_admin_password(password: str) -> bool:
    """
    Проверяет пароль администратора.
    """
    db = SessionLocal()
    try:
        setting_repo = SettingRepository(db)
        stored_hash = setting_repo.get('admin_password_hash')
        if not stored_hash:
            logger.error("Admin password hash not found in database.")
            return False
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying admin password: {e}")
        return False
    finally:
        db.close()

def verify_guard_password(password: str) -> bool:
    """
    Проверяет пароль для охранников.
    Если отдельный хеш не задан, использует пароль администратора.
    """
    db = SessionLocal()
    try:
        setting_repo = SettingRepository(db)
        stored_hash = setting_repo.get('guard_password_hash')
        if stored_hash:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        else:
            logger.warning("Guard password hash not found, falling back to admin password")
            return verify_admin_password(password)
    except Exception as e:
        logger.error(f"Error verifying guard password: {e}")
        return False
    finally:
        db.close()

def set_admin_password(new_password: str) -> bool:
    """
    Устанавливает новый пароль администратора.
    """
    db = SessionLocal()
    try:
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        setting_repo = SettingRepository(db)
        setting_repo.set('admin_password_hash', hashed, 'Хеш пароля администратора')
        logger.info("Admin password hash updated successfully.")
        return True
    except Exception as e:
        logger.error(f"Error setting admin password: {e}")
        return False
    finally:
        db.close()

def set_guard_password(new_password: str) -> bool:
    """
    Устанавливает новый пароль для охранников.
    """
    db = SessionLocal()
    try:
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        setting_repo = SettingRepository(db)
        setting_repo.set('guard_password_hash', hashed, 'Хеш пароля для охранников')
        logger.info("Guard password hash updated successfully.")
        return True
    except Exception as e:
        logger.error(f"Error setting guard password: {e}")
        return False
    finally:
        db.close()