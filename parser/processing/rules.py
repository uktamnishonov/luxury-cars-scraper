"""
Конфигурация правил обработки данных
Здесь вы можете определить свои кастомные функции обработки для каждого поля
"""

import re
from typing import Any, List, Optional

from parser.config.config import IMAGE_BASE_URL, IMAGE_PARAMS

# ==================== ВАШИ КАСТОМНЫЕ ПРАВИЛА ====================


def process_region_custom(value: Any) -> Optional[str]:
    """
    Кастомная обработка региона.
    Извлекает только первое слово (регион) из адреса

    Пример: '경기 수원시 권선구 권선로 308' -> '경기'
    """
    if not isinstance(value, str) or not value:
        return None

    # Берем первое слово
    region = value.split()[0] if value else None
    return region.strip() if region else None


def process_city_from_address(value: Any) -> Optional[str]:
    """
    Извлекает город (второе слово) из адреса

    Пример: '경기 수원시 권선구 권선로 308' -> '수원시'
    """
    if not isinstance(value, str) or not value:
        return None

    parts = value.split()
    if len(parts) >= 2:
        return parts[1].strip()
    return None


def process_model_name(value: Any) -> Optional[str]:
    """
    Обрабатывает название модели: убирает лишние символы
    """
    if not isinstance(value, str) or not value:
        return None

    # Убираем спецсимволы, оставляем только буквы, цифры и пробелы
    cleaned = re.sub(r"[^\w\s가-힣]", "", value)
    return cleaned.strip()


def process_grade_uppercase(value: Any) -> Optional[str]:
    """
    Приводит комплектацию к верхнему регистру
    """
    if not isinstance(value, str) or not value:
        return None

    return value.upper().strip()


def process_price_in_millions(value: Any) -> Optional[float]:
    """
    Конвертирует цену в миллионы (для удобства)
    Пример: 25000000 -> 25.0
    """
    if value is None:
        return None

    try:
        price = float(value) if isinstance(value, (int, float, str)) else None
        if price:
            return round(price / 1000000, 2)
    except (ValueError, TypeError):
        return None

    return None


def process_fuel_type_short(value: Any) -> Optional[str]:
    """
    Сокращает тип топлива
    Пример: 'Gasoline' -> 'Gas', 'Diesel' -> 'Die'
    """
    if not isinstance(value, str) or not value:
        return None

    fuel_map = {
        "Gasoline": "Gas",
        "Diesel": "Die",
        "Electric": "Elec",
        "Hybrid": "Hyb",
        "Plug-in Hybrid": "PHEV",
        "LPG": "LPG",
        "Hydrogen": "H2",
    }

    return fuel_map.get(value, value)


def process_transmission_short(value: Any) -> Optional[str]:
    """
    Сокращает тип КПП
    Пример: 'Automatic' -> 'AT', 'Manual' -> 'MT'
    """
    if not isinstance(value, str) or not value:
        return None

    trans_map = {
        "Automatic": "AT",
        "Manual": "MT",
        "CVT": "CVT",
        "DCT": "DCT",
        "AMT": "AMT",
    }

    return trans_map.get(value, value)


def process_mileage_in_thousands(value: Any) -> Optional[float]:
    """
    Конвертирует пробег в тысячи км
    Пример: 50000 -> 50.0
    """
    if value is None:
        return None

    try:
        mileage = float(value) if isinstance(value, (int, float, str)) else None
        if mileage:
            return round(mileage / 1000, 1)
    except (ValueError, TypeError):
        return None

    return None


def process_photos_sorted(value: Any) -> Optional[List[str]]:
    """Сортирует фото по коду"""
    if not value or not isinstance(value, list):
        return []

    # Сортируем по коду
    sorted_photos = sorted(value, key=lambda x: x.get("code", "999"))

    image_urls = []

    for photo in sorted_photos:
        if not isinstance(photo, dict):
            continue

        path = photo.get("path")
        if not path:
            continue

        full_url = f"{IMAGE_BASE_URL}{path}{IMAGE_PARAMS}"
        image_urls.append(full_url)

    return image_urls


def process_vin_masked(value: Any) -> Optional[str]:
    """
    Маскирует VIN (оставляет только первые и последние 4 символа)
    Пример: 'KMHXX00XXXX000000' -> 'KMHX***********000'
    """
    if not isinstance(value, str) or not value:
        return None

    vin = value.strip().upper()

    if len(vin) < 8:
        return vin

    # Маскируем средние символы
    masked = vin[:4] + "*" * (len(vin) - 7) + vin[-3:]
    return masked


# ==================== СЛОВАРЬ ПРАВИЛ ====================

# Здесь вы определяете, какая функция применяется к какому полю
# Формат: "название_поля": функция_обработки

CUSTOM_PROCESSING_RULES = {
    # Регион - берем только первое слово
    "region": process_region_custom,
    # Фотографии - преобразуем в полные URL
    "images": process_photos_sorted,
    # Цена - можете выбрать один из вариантов:
    # "price": process_price_in_millions,  # В миллионах
    # "price": lambda v: int(v) if v else None,  # Просто int
    # Пробег - можете выбрать:
    # "mileage": process_mileage_in_thousands,  # В тысячах
    # "mileage": lambda v: int(v) if v else None,  # Просто int
    # VIN - маскировка (если нужна конфиденциальность)
    # "vin": process_vin_masked,
    # Модель - очистка от лишних символов
    # "model": process_model_name,
    # Комплектация - в верхний регистр
    # "grade": process_grade_uppercase,
    # Топливо - сокращенная версия (после перевода)
    # "fuel": process_fuel_type_short,
    # КПП - сокращенная версия (после перевода)
    # "transmission": process_transmission_short,
}


# ==================== ФИЛЬТРЫ ДАННЫХ ====================


class DataFilter:
    """
    Класс для фильтрации данных по заданным условиям
    """

    @staticmethod
    def filter_by_year(
        data: dict, min_year: Optional[int] = None, max_year: Optional[int] = None
    ) -> bool:
        """Фильтрует по году выпуска"""
        year = data.get("year")
        if year is None:
            return True

        if min_year and year < min_year:
            return False
        if max_year and year > max_year:
            return False

        return True

    @staticmethod
    def filter_by_mileage(data: dict, max_mileage: Optional[int] = None) -> bool:
        """Фильтрует по пробегу"""
        mileage = data.get("mileage")
        if mileage is None:
            return True

        if max_mileage and mileage > max_mileage:
            return False

        return True

    @staticmethod
    def filter_by_price(
        data: dict, min_price: Optional[int] = None, max_price: Optional[int] = None
    ) -> bool:
        """Фильтрует по цене"""
        price = data.get("price")
        if price is None:
            return True

        if min_price and price < min_price:
            return False
        if max_price and price > max_price:
            return False

        return True

    @staticmethod
    def filter_by_brand(data: dict, allowed_brands: Optional[list] = None) -> bool:
        """Фильтрует по бренду"""
        if not allowed_brands:
            return True

        brand = data.get("brand")
        if not brand:
            return True

        return brand in allowed_brands

    @staticmethod
    def filter_by_fuel(data: dict, allowed_fuels: Optional[list] = None) -> bool:
        """Фильтрует по типу топлива"""
        if not allowed_fuels:
            return True

        fuel = data.get("fuel")
        if not fuel:
            return True

        return fuel in allowed_fuels


# Конфигурация фильтров (включайте/выключайте по необходимости)
FILTER_CONFIG = {
    "enabled": False,  # Включить/выключить фильтрацию
    "min_year": 2020,
    "max_year": None,
    "max_mileage": 100000,  # 100,000 км
    "min_price": 1000,
    "max_price": None,
    "allowed_brands": None,  # None = все бренды, или ['Hyundai', 'Kia']
    "allowed_fuels": None,  # None = все типы, или ['Gasoline', 'Diesel']
    "process_photos_sorted": True,
}


def apply_filters(data: dict, config: dict = FILTER_CONFIG) -> bool:
    """
    Применяет все фильтры к данным

    Args:
        data: Словарь с данными автомобиля
        config: Конфигурация фильтров

    Returns:
        True если данные прошли фильтры, False если нет
    """
    if not config.get("enabled", False):
        return True

    filters = [
        DataFilter.filter_by_year(data, config.get("min_year"), config.get("max_year")),
        DataFilter.filter_by_mileage(data, config.get("max_mileage")),
        DataFilter.filter_by_price(
            data, config.get("min_price"), config.get("max_price")
        ),
        DataFilter.filter_by_brand(data, config.get("allowed_brands")),
        DataFilter.filter_by_fuel(data, config.get("allowed_fuels")),
    ]

    return all(filters)
