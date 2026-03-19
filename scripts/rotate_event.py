import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.anonymize_service import anonymize_past_events
import logging
logging.basicConfig(
    filename='/opt/max_bot_pass/logs/anonymize.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

if __name__ == "__main__":
    anonymize_past_events()