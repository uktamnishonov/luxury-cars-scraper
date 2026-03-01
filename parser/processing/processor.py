"""
Модуль для обработки и фильтрации данных перед сохранением
Позволяет применять кастомные правила обработки для каждого поля
"""

import re
from typing import Any, Callable, Dict, Optional

from logger.logging import get_parser_logger

logger = get_parser_logger(__name__)


class DataProcessor:
    """
    Класс для обработки данных с применением кастомных правил
    """

    def __init__(self, processing_rules: Optional[Dict[str, Callable]] = None):
        """
        Args:
            processing_rules: Словарь {название_поля: функция_обработки}
        """
        self.processing_rules = processing_rules or {}
        self.default_rules = self._get_default_rules()

        # Статистика
        self.stats = {
            "processed_fields": 0,
            "applied_rules": 0,
        }

    def _get_default_rules(self) -> Dict[str, Callable]:
        """
        Возвращает набор стандартных правил обработки
        Вы можете переопределить их через processing_rules при инициализации
        """
        return {
            "region": self._process_region,
            "price": self._process_price,
            "mileage": self._process_mileage,
            "year": self._process_year,
            "vin": self._process_vin,
            "color": self._process_color,
            "displacement": self._process_displacement,
            "images": self._process_photos,  # Обработка фотографий
        }

    # ==================== ПРАВИЛА ОБРАБОТКИ ====================

    @staticmethod
    def _process_region(value: Any) -> Optional[str]:
        """
        Извлекает только регион (первое слово) из полного адреса
        Пример: '경기 수원시 권선구 권선로 308' -> '경기'
        """
        if not isinstance(value, str) or not value:
            return None

        # Берем первое слово (регион)
        region = value.split()[0] if value else None
        return region.strip() if region else None

    @staticmethod
    def _process_price(value: Any) -> Optional[int]:
        """
        Обрабатывает цену: удаляет нечисловые символы, конвертирует в int
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return int(value)

        if isinstance(value, str):
            # Удаляем все кроме цифр
            price_str = re.sub(r"\D", "", value)
            try:
                return int(price_str) if price_str else None
            except ValueError:
                return None

        return None

    @staticmethod
    def _process_mileage(value: Any) -> Optional[int]:
        """
        Обрабатывает пробег: конвертирует в int
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return int(value)

        if isinstance(value, str):
            # Удаляем все кроме цифр
            mileage_str = re.sub(r"\D", "", value)
            try:
                return int(mileage_str) if mileage_str else None
            except ValueError:
                return None

        return None

    @staticmethod
    def _process_year(value: Any) -> Optional[int]:
        """
        Обрабатывает год: извлекает 4 цифры или берет первые 4 символа
        Пример: '202506' -> 2025, '2025' -> 2025
        """
        if value is None:
            return None

        if isinstance(value, int):
            # Если число больше 9999, берем первые 4 цифры
            if value > 9999:
                return int(str(value)[:4])
            return value

        if isinstance(value, str):
            # Извлекаем первые 4 цифры
            year_match = re.search(r"\d{4}", value)
            if year_match:
                return int(year_match.group())

        return None

    @staticmethod
    def _process_vin(value: Any) -> Optional[str]:
        """
        Обрабатывает VIN: приводит к верхнему регистру, убирает пробелы
        """
        if not isinstance(value, str) or not value:
            return None

        return value.strip().upper()

    @staticmethod
    def _process_color(value: Any) -> Optional[str]:
        """
        Обрабатывает цвет: убирает лишние пробелы
        """
        if not isinstance(value, str) or not value:
            return None

        return value.strip()

    @staticmethod
    def _process_displacement(value: Any) -> Optional[int]:
        """
        Обрабатывает объем двигателя: конвертирует в int (cc)
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return int(value)

        if isinstance(value, str):
            # Удаляем все кроме цифр
            disp_str = re.sub(r"\D", "", value)
            try:
                return int(disp_str) if disp_str else None
            except ValueError:
                return None

        return None

    @staticmethod
    def _process_photos(value: Any) -> Optional[list]:
        """
        Обрабатывает массив фотографий (fallback если не используется кастомное правило)
        Возвращает как есть или пустой список
        """
        if isinstance(value, list):
            return value
        return []

    # ==================== МЕТОДЫ ОБРАБОТКИ ====================

    def process_field(self, field_name: str, value: Any) -> Any:
        """
        Применяет правило обработки для конкретного поля

        Args:
            field_name: Название поля
            value: Значение поля

        Returns:
            Обработанное значение
        """
        # Сначала проверяем кастомные правила
        if field_name in self.processing_rules:
            try:
                processed_value = self.processing_rules[field_name](value)
                self.stats["applied_rules"] += 1
                return processed_value
            except Exception as e:
                logger.error(f"Ошибка обработки поля '{field_name}': {e}")
                return value

        # Затем проверяем стандартные правила
        if field_name in self.default_rules:
            try:
                processed_value = self.default_rules[field_name](value)
                self.stats["applied_rules"] += 1
                return processed_value
            except Exception as e:
                logger.error(f"Ошибка обработки поля '{field_name}': {e}")
                return value

        # Если правил нет, возвращаем как есть
        return value

    def process_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает все поля в словаре

        Args:
            data: Словарь с данными

        Returns:
            Словарь с обработанными данными
        """
        processed = {}

        for field_name, value in data.items():
            processed[field_name] = self.process_field(field_name, value)
            self.stats["processed_fields"] += 1

        return processed

    def add_rule(self, field_name: str, processing_func: Callable):
        """
        Добавляет новое правило обработки

        Args:
            field_name: Название поля
            processing_func: Функция обработки
        """
        self.processing_rules[field_name] = processing_func
        logger.info(f"Добавлено правило обработки для поля '{field_name}'")

    def remove_rule(self, field_name: str):
        """Удаляет правило обработки"""
        if field_name in self.processing_rules:
            del self.processing_rules[field_name]
            logger.info(f"Удалено правило обработки для поля '{field_name}'")

    def get_statistics(self) -> Dict[str, int]:
        """Возвращает статистику обработки"""
        return self.stats.copy()

    def print_statistics(self):
        """Выводит статистику в лог"""
        stats = self.get_statistics()
        logger.info("=" * 60)
        logger.info("📊 СТАТИСТИКА ОБРАБОТКИ ДАННЫХ:")
        logger.info(f"  Обработано полей: {stats['processed_fields']}")
        logger.info(f"  Применено правил: {stats['applied_rules']}")
        logger.info("=" * 60)


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================


def create_custom_processor() -> DataProcessor:
    """
    Создает процессор с кастомными правилами
    Используйте эту функцию для определения своих правил обработки
    """
    # Пример кастомных правил
    custom_rules = {
        # Можете добавить свои правила здесь
        # "field_name": lambda value: your_processing_logic(value),
    }

    return DataProcessor(processing_rules=custom_rules)


# ==================== ПРИМЕРЫ КАСТОМНЫХ ФУНКЦИЙ ====================


def extract_city_from_address(value: str) -> Optional[str]:
    """
    Пример: извлекает город из адреса
    '경기 수원시 권선구 권선로 308' -> '수원시'
    """
    if not isinstance(value, str) or not value:
        return None

    parts = value.split()
    if len(parts) >= 2:
        return parts[1]
    return None


def normalize_phone_number(value: str) -> Optional[str]:
    """
    Пример: нормализует номер телефона
    '010-1234-5678' -> '01012345678'
    """
    if not isinstance(value, str) or not value:
        return None

    return re.sub(r"\D", "", value)


def capitalize_names(value: str) -> Optional[str]:
    """
    Пример: приводит имена к правильному регистру
    'john doe' -> 'John Doe'
    """
    if not isinstance(value, str) or not value:
        return None

    return value.title()
