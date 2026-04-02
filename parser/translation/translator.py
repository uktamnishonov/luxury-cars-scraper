"""
Модуль для перевода корейских терминов на английский.
Использует категоризированные словари для эффективного поиска
"""

import json
from typing import Any, Dict, Optional

from deep_translator import GoogleTranslator

from logger.logging import get_parser_logger
from config.paths import PARSER_TRANSLATION_DIR
from parser.translation import cache

logger = get_parser_logger(__name__)

# Файл для хранения новых переводов, которые не нашлись в кеше
MISSING_TRANSLATIONS_FILE = PARSER_TRANSLATION_DIR / 'missing.json'


class Translator:
    """
    Переводчик с категоризированным кешем
    Автоматически определяет категорию по ключу поля
    """

    def __init__(self):
        self.category_map = cache.CATEGORY_MAP
        self.general_cache = cache.GENERAL
        self.missing_translations: Dict[str, set] = {}
        self._load_missing_translations()

        # Статистика
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def _load_missing_translations(self):
        """Загружает список непереведенных терминов"""
        if MISSING_TRANSLATIONS_FILE.exists():
            try:
                with open(MISSING_TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Конвертируем списки обратно в sets
                    self.missing_translations = {k: set(v) for k, v in data.items()}
                    total_missing = sum(
                        len(v) for v in self.missing_translations.values()
                    )
                    logger.info(f"Загружено {total_missing} непереведенных терминов")
            except Exception as e:
                logger.error(f"Ошибка загрузки missing_translations: {e}")

    def _save_missing_translations(self):
        """Сохраняет список непереведенных терминов"""
        try:
            # Конвертируем sets в списки для JSON
            data = {k: sorted(list(v)) for k, v in self.missing_translations.items()}

            with open(MISSING_TRANSLATIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(
                f"Сохранены непереведенные термины в {MISSING_TRANSLATIONS_FILE}"
            )
        except Exception as e:
            logger.error(f"Ошибка сохранения missing_translations: {e}")

    def translate(self, text: str, field_name: Optional[str] = None) -> str:
        if not text or not isinstance(text, str):
            return text

        self.stats["total_requests"] += 1
        text = text.strip()

        if text.isascii():
            return text

        # Проверяем категорийные словари
        if field_name and field_name in self.category_map:
            category_dict = self.category_map[field_name]
            if text in category_dict:
                self.stats["cache_hits"] += 1
                return category_dict[text]

        # Проверяем общий словарь
        if text in self.general_cache:
            self.stats["cache_hits"] += 1
            return self.general_cache[text]

        # Проверяем все категории (медленно)
        for category_dict in self.category_map.values():
            if text in category_dict:
                self.stats["cache_hits"] += 1
                return category_dict[text]

        # Если перевод не найден, обращаемся к deep-translator
        try:
            translated = GoogleTranslator(source="ko", target="en").translate(text)
            self.stats["cache_misses"] += 1
            logger.info(f"Переведено через API: '{text}' -> '{translated}'")

            # Сохраняем в GENERAL или в категорию, если есть field_name
            if field_name and field_name in self.category_map:
                self.category_map[field_name][text] = translated
            else:
                self.general_cache[text] = translated

            return translated

        except Exception:
            # Если не удалось перевести через API, добавляем в missing
            self.stats["cache_misses"] += 1
            category = field_name or "unknown"
            if category not in self.missing_translations:
                self.missing_translations[category] = set()
            if text not in self.missing_translations[category]:
                self.missing_translations[category].add(text)
                self._save_missing_translations()
                logger.warning(
                    f"Не найден перевод и API упал для '{text}' (категория: {category})"
                )

            return text

    def translate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Переводит все строковые значения в словаре
        Использует ключи словаря как названия полей для определения категории

        Args:
            data: Словарь с данными

        Returns:
            Словарь с переведенными значениями
        """
        translated = {}

        for key, value in data.items():
            try:
                if isinstance(value, str):
                    translated[key] = self.translate(value, field_name=key)
                elif isinstance(value, dict):
                    translated[key] = self.translate_dict(value)
                elif isinstance(value, list):
                    translated_list = []
                    for item in value:
                        try:
                            if isinstance(item, str):
                                translated_list.append(self.translate(item, field_name=key))
                            else:
                                translated_list.append(item)
                        except Exception as e:
                            logger.error(f"Error translating list item in '{key}': {e}")
                            translated_list.append(item)
                    translated[key] = translated_list
                else:
                    translated[key] = value
            except Exception as e:
                logger.error(f"Error translating key '{key}': {e}")
                translated[key] = value

        return translated

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику использования"""
        cache_hit_rate = (
            (self.stats["cache_hits"] / self.stats["total_requests"] * 100)
            if self.stats["total_requests"] > 0
            else 0
        )

        return {
            **self.stats,
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "unique_missing": sum(len(v) for v in self.missing_translations.values()),
        }

    def print_statistics(self):
        """Выводит статистику в лог"""
        stats = self.get_statistics()
        logger.info("=" * 60)
        logger.info("📊 СТАТИСТИКА ПЕРЕВОДОВ:")
        logger.info(f"  Всего запросов: {stats['total_requests']}")
        logger.info(f"  Найдено в кеше: {stats['cache_hits']}")
        logger.info(f"  Не найдено: {stats['cache_misses']}")
        logger.info(f"  Процент попаданий: {stats['cache_hit_rate']}")
        logger.info(f"  Уникальных непереведенных: {stats['unique_missing']}")
        logger.info("=" * 60)