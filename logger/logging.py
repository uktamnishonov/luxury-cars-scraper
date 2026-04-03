"""
Централизованная система логирования для всего проекта
"""
import logging
import sys
import platform
import io
from pathlib import Path
from typing import Optional

from config.paths import PARSER_FILE_LOG, BOT_FILE_LOG

# Windows encoding fix for emoji/UTF-8 output (only wrap once, with error handling)
if platform.system() == "Windows" and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        # Already wrapped or no buffer available
        pass


def setup_logger(
        name: str,
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        console: bool = True
) -> logging.Logger:
    """
    Настраивает и возвращает логгер

    Args:
        name: Имя логгера (обычно __name__ модуля)
        level: Уровень логирования (INFO, DEBUG, ERROR, etc.)
        log_file: Путь к файлу логов (опционально)
        console: Выводить ли логи в консоль

    Returns:
        Настроенный logger

    Пример:
        from logger.logging import setup_logger
        logger = setup_logger(__name__)
        logger.info("Сообщение")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Убираем старые handlers (если переинициализация)
    logger.handlers.clear()

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Консольный вывод с UTF-8 поддержкой
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        # Ensure UTF-8 for Windows
        if platform.system() == "Windows":
            console_handler.setLevel(level)
        logger.addHandler(console_handler)

    # Файловый вывод
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Предустановленные логгеры для быстрого использования
def get_parser_logger(module_name: str) -> logging.Logger:
    """Логгер для модулей парсера"""
    return setup_logger(
        name=f"parser.{module_name}",
        log_file=PARSER_FILE_LOG,
    )


def get_bot_logger(module_name: str) -> logging.Logger:
    """Логгер для модулей бота"""
    return setup_logger(
        name=f"bot.{module_name}",
        log_file=BOT_FILE_LOG,
        level=logging.DEBUG,
    )