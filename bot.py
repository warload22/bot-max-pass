from flask import Flask
from app.api.routes import webhook_bp, qr_scan_bp
from app.core.config import Config
import logging
import os
import traceback

def create_app():
    app = Flask(__name__, template_folder='app/templates')
    app.config.from_object(Config)
    app.secret_key = Config.APP_SECRET

    # Настройка логирования
    if not os.path.exists(Config.LOG_DIR):
        os.makedirs(Config.LOG_DIR)
    logging.basicConfig(
        filename=os.path.join(Config.LOG_DIR, 'app.log'),
        level=logging.DEBUG if Config.DEBUG else logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

    # Регистрация blueprint'ов
    app.register_blueprint(webhook_bp, url_prefix='/webhook2')
    app.register_blueprint(qr_scan_bp, url_prefix='/qr-scan')

    # Глобальный обработчик исключений
    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
        if Config.DEBUG:
            return f"Internal Server Error: {e}\n{traceback.format_exc()}", 500
        return "Internal Server Error", 500

    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f"Internal Server Error: {error}")
        return "Internal Server Error", 500

    @app.errorhandler(404)
    def not_found(error):
        return "Not Found", 404

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5001, debug=Config.DEBUG)