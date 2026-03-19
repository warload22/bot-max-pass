import requests
import logging
import time
from app.core.config import Config

BASE_URL = "https://platform-api.max.ru"

def get_upload_url(file_type="image"):
    """
    Запрашивает URL для загрузки файла указанного типа.
    Токен передаётся в query-параметре access_token.
    Возвращает (upload_url, token) или (None, None) при ошибке.
    Для изображений токен может отсутствовать.
    """
    url = f"{BASE_URL}/uploads"
    params = {
        "type": file_type,
        "access_token": Config.MAX_BOT_TOKEN
    }
    try:
        response = requests.post(url, params=params)
        logging.debug(f"get_upload_url response: {response.status_code} {response.text}")
        response.raise_for_status()
        data = response.json()
        upload_url = data.get('url')
        token = data.get('token')
        return upload_url, token
    except Exception as e:
        logging.error(f"Error getting upload URL: {e}")
        return None, None

def upload_file_to_url(upload_url, file_bytes, filename="qr.png", content_type="image/png"):
    """
    Загружает файл по полученному URL.
    Возвращает JSON ответа от сервера (содержит token, photo_id и т.п.) или None.
    """
    try:
        # Для multipart upload используем files
        files = {'data': (filename, file_bytes, content_type)}
        response = requests.post(upload_url, files=files)
        logging.debug(f"upload_file_to_url response: {response.status_code} {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        return None

def send_photo(chat_id, photo_bytes, caption=None):
    """
    Отправляет фотографию (QR-код) в чат, следуя процессу:
    1. Получить URL для загрузки.
    2. Загрузить файл.
    3. Извлечь токен из ответа загрузки.
    4. Отправить сообщение с attachment, используя полученный токен.
    """
    # Шаг 1: получаем URL для загрузки
    upload_url, _ = get_upload_url("image")
    if not upload_url:
        logging.error("Failed to get upload URL")
        return None

    # Шаг 2: загружаем файл
    upload_response = upload_file_to_url(upload_url, photo_bytes)
    if not upload_response:
        logging.error("Failed to upload file")
        return None

    # Шаг 3: извлекаем токен из ответа (структура: {"photos": {"photoId": {"token": "..."}}})
    token = None
    if 'photos' in upload_response:
        # Берём первый (и единственный) ключ внутри photos
        for photo_id, photo_data in upload_response['photos'].items():
            token = photo_data.get('token')
            if token:
                break
    if not token:
        logging.error(f"No token in upload response: {upload_response}")
        return None

    # Небольшая пауза для обработки файла сервером (рекомендация из документации)
    time.sleep(1)

    # Шаг 4: отправляем сообщение с вложением
    message_url = f"{BASE_URL}/messages"
    params = {
        "chat_id": chat_id,
        "access_token": Config.MAX_BOT_TOKEN
    }
    attachment = {
        "type": "image",
        "payload": {
            "token": token
        }
    }
    payload = {"attachments": [attachment]}
    if caption:
        payload["text"] = caption
        payload["format"] = "html"

    try:
        response = requests.post(message_url, params=params, json=payload)
        logging.debug(f"send_photo final response: {response.status_code} {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error sending photo message: {e}")
        return None

def send_message(chat_id, text, keyboard=None):
    url = f"{BASE_URL}/messages"
    params = {
        "chat_id": chat_id,
        "access_token": Config.MAX_BOT_TOKEN
    }
    payload = {
        "text": text,
        "format": "html"
    }
    if keyboard:
        payload["attachments"] = [keyboard]  # keyboard уже содержит {type, payload}

    logging.debug(f"Sending payload to {chat_id}: {payload}")

    try:
        response = requests.post(url, params=params, json=payload)
        response.raise_for_status()
        logging.info(f"Message sent to {chat_id}, status: {response.status_code}")
        return response.json()
    except Exception as e:
        logging.error(f"Error sending message to {chat_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response body: {e.response.text}")
        return None

def delete_message(chat_id, message_id):
    url = f"{BASE_URL}/messages"
    params = {
        "message_id": message_id,
        "access_token": Config.MAX_BOT_TOKEN
    }

    try:
        response = requests.delete(url, params=params)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"Error deleting message {message_id}: {e}")
        return False

def send_document(chat_id, file_bytes, filename, caption=None):
    """
    Отправляет файл (Excel) в чат.
    Процесс: получить URL для загрузки (type=file), загрузить, получить токен, отправить сообщение.
    """
    # Получаем URL для загрузки
    upload_url, _ = get_upload_url("file")
    if not upload_url:
        logging.error("Failed to get upload URL for file")
        return None

    # Загружаем файл
    upload_response = upload_file_to_url(upload_url, file_bytes, filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if not upload_response:
        logging.error("Failed to upload file")
        return None

    # Извлекаем токен (в ответе может быть поле 'token' или другое)
    token = upload_response.get('token')
    if not token:
        # Если нет токена, возможно, ответ содержит другой идентификатор
        # Например, для файлов может быть поле 'file_id'?
        logging.error(f"No token in upload response: {upload_response}")
        return None

    # Небольшая пауза
    time.sleep(1)

    # Отправляем сообщение с вложением
    message_url = f"{BASE_URL}/messages"
    params = {"chat_id": chat_id, "access_token": Config.MAX_BOT_TOKEN}
    attachment = {
        "type": "file",
        "payload": {"token": token}
    }
    payload = {"attachments": [attachment]}
    if caption:
        payload["text"] = caption
        payload["format"] = "html"

    try:
        response = requests.post(message_url, params=params, json=payload)
        logging.debug(f"send_document response: {response.status_code} {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error sending document: {e}")
        return None