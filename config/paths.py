from pathlib import Path
from datetime import datetime


def get_timestamped_filename(base_name: str, extension: str = "json") -> str:
    """Generate filename with timestamp: base_name_YYYYMMDD_HHMMSS.extension"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"


# Общие пути
BASE_DIR = Path(__file__).resolve().parent.parent
PARSER_DIR = BASE_DIR / "parser"
BOT_DIR = BASE_DIR / "bot"
LOGS_DIR = BASE_DIR / "logs"
LOGGER_DIR = BASE_DIR / "logger"
PARSER_FILE_LOG = LOGS_DIR / "parser.log"
BOT_FILE_LOG = LOGS_DIR / "bot.log"
DATA_DIR = BASE_DIR / "data"

# Legacy file paths (for backward compatibility)
IDS_FILE = DATA_DIR / "car_ids.json"
DUPLICATED_IDS_FILE = DATA_DIR / "duplicated_ids.json"
DATA_DETAILS_DIR = DATA_DIR / "details"


# Пути парсера
PARSER_TRANSLATION_DIR = PARSER_DIR / "translation"
PARSER_COOKIES_DIR = PARSER_DIR / "scripts" / "cookies"

# Пути бота
