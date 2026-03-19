import qrcode
from io import BytesIO
from app.core.config import Config

def generate_qr_code(data: str) -> bytes:
    """
    Генерирует QR-код из строки data и возвращает байты PNG-изображения.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    byte_io = BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)
    return byte_io.getvalue()

def generate_qr_for_registration(reg_uuid) -> bytes:
    """
    Генерирует QR-код для регистрации: встраивает ссылку с UUID.
    Возвращает байты PNG.
    """
    url = f"{Config.QR_BASE_URL}?uid={reg_uuid}"
    return generate_qr_code(url)