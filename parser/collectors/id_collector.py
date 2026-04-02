"""
Модуль для сбора ID автомобилей из списка
"""

import json
from typing import List, Set, Dict

from parser.api.client import EncarAPIClient
from parser.config.config import PARAMS, SEARCH_PARAMS
from config.paths import (
    DATA_DIR,
    IDS_FILE,
    DUPLICATED_IDS_FILE,
    get_timestamped_filename,
)
from logger.logging import get_parser_logger


logger = get_parser_logger(__name__)


class CarIDCollector:
    """Класс для сбора ID автомобилей"""

    def __init__(self, use_timestamp: bool = True):
        self.client = EncarAPIClient()
        self.collected_ids: Set[str] = set()
        self.duplicated_ids: Dict[str, str] = {}
        self.use_timestamp = use_timestamp

        # Generate timestamped filenames if enabled
        if use_timestamp:
            self.ids_file = DATA_DIR / get_timestamped_filename("car_ids")
            self.duplicated_ids_file = DATA_DIR / get_timestamped_filename(
                "duplicated_ids"
            )
        else:
            self.ids_file = IDS_FILE
            self.duplicated_ids_file = DUPLICATED_IDS_FILE

        self._ensure_data_dir()

    @staticmethod
    def _ensure_data_dir():
        """Создает директорию для данных если её нет"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _load_existing_ids() -> Set[str]:
        """Загружает уже собранные ID из файла"""
        try:
            if IDS_FILE.exists():
                with open(IDS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.get("ids", []))
        except Exception as e:
            logger.error(f"Ошибка загрузки существующих ID: {e}")

        return set()

    def _save_ids(self):
        """Сохраняет собранные ID в JSON файл"""
        try:
            data = {
                "total_count": len(self.collected_ids),
                "ids": sorted(list(self.collected_ids)),
            }

            # Сохраняем в timestamped файл
            with open(self.ids_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Сохранено {len(self.collected_ids)} ID в {self.ids_file}")

            # Также сохраняем в legacy файл для совместимости
            if self.use_timestamp:
                with open(IDS_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"Также сохранено в legacy файл: {IDS_FILE}")

        except Exception as e:
            logger.error(f"Ошибка сохранения ID: {e}")

    def _save_duplicated_ids(self):
        """Сохраняет дублированные ID в JSON файл"""
        try:
            # Сохраняем в timestamped файл
            with open(self.duplicated_ids_file, "w", encoding="utf-8") as f:
                json.dump(self.duplicated_ids, f, ensure_ascii=False, indent=2)

            logger.info(
                f"Сохранено {len(self.duplicated_ids)} дублированных ID в {self.duplicated_ids_file}"
            )

            # Также сохраняем в legacy файл для совместимости
            if self.use_timestamp:
                with open(DUPLICATED_IDS_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.duplicated_ids, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Ошибка сохранения дублированных ID: {e}")

    def _get_ids(
        self,
        sell_type: str,
        brand: str,
        model: str,
        current_count: int,
        year_from: int = None,
    ):
        start = 0
        total_cars = None

        year_info = f", год от: {year_from}" if year_from else ""
        logger.info(
            f"📦 Начинаем сбор ID для бренда: {brand}, модель: {model}, тип продажи: {sell_type}{year_info}"
        )

        while True:
            try:
                # Получаем порцию данных
                response = self.client.get_car_list(
                    sell_type=sell_type,
                    brand=brand,
                    model=model,
                    start=start,
                    count=current_count,
                    year_from=year_from,
                )

                if not response:
                    logger.warning(f"Не удалось получить данные для offset {start}")
                    break

                # Получаем общее количество при первом запросе
                if total_cars is None:
                    total_cars = response.get("Count", 0)
                    logger.info(f"Всего автомобилей найдено: {total_cars}")

                # Извлекаем ID из результатов
                search_results = response.get("SearchResults", [])

                if not search_results:
                    logger.info("Больше нет результатов")
                    break

                new_ids = 0
                dup_ids = 0
                for car in search_results:
                    try:
                        car_id = str(car.get("Id", ""))
                        if car.get("ServiceCopyCar") == "DUPLICATION":
                            original_id = str(car.get("Photo", "")).split(sep="/")[-1][:-1]
                            self.duplicated_ids[original_id] = car_id
                            dup_ids += 1
                        else:
                            if car_id and car_id not in self.collected_ids:
                                self.collected_ids.add(car_id)
                                new_ids += 1
                    except Exception as e:
                        logger.error(f"Error processing car data: {e}")
                        continue

                logger.info(
                    f"Обработано {len(search_results)} результатов. "
                    f"Новых ID: {new_ids}, всего собрано: {len(self.collected_ids)}. "
                    f"Дублированных ID: {dup_ids}, всего собрано дублированных: {len(self.duplicated_ids)}"
                )

                # Переходим к следующей порции
                start += current_count

                # Проверяем, достигли ли конца
                if start >= total_cars:
                    logger.info("Достигнут конец списка")
                    break

            except Exception as e:
                logger.error(f"Error fetching IDs from API: {e}")
                break

    def collect_all_ids(self, append_mode: bool = False) -> List[str]:
        """
        Собирает все ID автомобилей

        Args:
            append_mode: Если True, добавляет к существующим ID, иначе перезаписывает

        Returns:
            Список всех собранных ID
        """
        if append_mode:
            self.collected_ids = self._load_existing_ids()
            logger.info(f"Загружено {len(self.collected_ids)} существующих ID")

        sell_type = SEARCH_PARAMS["sell_type"]
        current_count = SEARCH_PARAMS["current_count"]

        logger.info(f"{'=' * 50}")
        logger.info(f"Начало сбора айди автомобилей.")
        logger.info(f"{'=' * 50}")

        for brand, brand_params in PARAMS.items():
            # Извлекаем параметры для бренда
            if isinstance(brand_params, dict):
                year_from = brand_params.get("year_from")
                models = brand_params.get(
                    "models", ""
                )  # Пустая строка означает все модели
            else:
                # Поддержка старого формата (строка или список)
                year_from = None
                models = brand_params

            # Обрабатываем модели
            if isinstance(models, list):
                for model in models:
                    try:
                        self._get_ids(sell_type, brand, model, current_count, year_from)
                    except Exception as e:
                        logger.error(f"Ошибка при обработке {brand} {model}: {e}")
            else:
                try:
                    model = models
                    self._get_ids(sell_type, brand, model, current_count, year_from)
                except Exception as e:
                    logger.error(f"Ошибка при обработке {brand}: {e}")

        self._save_ids()
        self._save_duplicated_ids()
        logger.info(
            f"Сбор завершен. Итого уникальных ID: {len(self.collected_ids)}. "
            f"Итого дублированных ID: {len(self.duplicated_ids)}"
        )

        return sorted(list(self.collected_ids))

    def get_collected_ids(self) -> List[str]:
        """Возвращает список собранных ID"""
        return sorted(list(self.collected_ids))

    def close(self):
        """Закрывает соединения"""
        self.client.close()
