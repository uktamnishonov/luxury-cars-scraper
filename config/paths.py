from pathlib import Path

# Общие пути
BASE_DIR = Path(__file__).resolve().parent.parent
PARSER_DIR = BASE_DIR / "parser"
BOT_DIR = BASE_DIR / "bot"
LOGS_DIR = BASE_DIR / "logs"
LOGGER_DIR = BASE_DIR / "logger"
PARSER_FILE_LOG = LOGS_DIR / "parser.log"
BOT_FILE_LOG = LOGS_DIR / "bot.log"
DATA_DIR = BASE_DIR / "data"
IDS_FILE = DATA_DIR / "car_ids.json"
DUPLICATED_IDS_FILE = DATA_DIR / "duplicated_ids.json"
DATA_DETAILS_DIR = DATA_DIR / "details"


# Пути парсера
PARSER_TRANSLATION_DIR = PARSER_DIR / "translation"
PARSER_COOKIES_DIR = PARSER_DIR / "scripts" / "cookies"

# Пути бота
