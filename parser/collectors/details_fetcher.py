"""
Модуль для получения детальной информации об автомобилях
"""

import json
from datetime import datetime
from typing import List, Optional, Set

from logger.logging import get_parser_logger
from config.paths import DATA_DETAILS_DIR, IDS_FILE, get_timestamped_filename

from parser.api.client import EncarAPIClient
from parser.config.config import FIELDS_TO_EXTRACT, SMALL_FIELDS_TO_EXTRACT, OPTIONS
from parser.processing.processor import DataProcessor
from parser.processing.rules import (
    CUSTOM_PROCESSING_RULES,
    FILTER_CONFIG,
    apply_filters,
)
from parser.translation.translator import Translator


logger = get_parser_logger(__name__)


class VehicleDetailsFetcher:
    """Класс для получения детальной информации об автомобилях"""

    def __init__(
        self,
        output_file: str = None,
        check_history: bool = True,
        use_timestamp: bool = True,
    ):
        self.client = EncarAPIClient()
        self.translator = Translator()
        self.processor = DataProcessor(processing_rules=CUSTOM_PROCESSING_RULES)

        # Generate timestamped filename if enabled and no output_file specified
        if use_timestamp and output_file is None:
            self.output_file = get_timestamped_filename("cars_data", "jsonl")
        elif output_file is None:
            self.output_file = "cars_data.jsonl"
        else:
            self.output_file = output_file

        self.check_history = check_history
        self._ensure_details_dir()

        # Статистика фильтрации
        self.filter_stats = {
            "total_processed": 0,
            "filtered_out": 0,
        }

    def _ensure_details_dir(self):
        """Создает директорию для деталей если её нет"""
        DATA_DETAILS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_ids(self) -> List[str]:
        """Загружает список ID из файла"""
        try:
            if not IDS_FILE.exists():
                logger.error(f"Файл {IDS_FILE} не найден. Сначала запустите сбор ID.")
                return []

            with open(IDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                ids = data.get("ids", [])
                logger.info(f"Загружено {len(ids)} ID для обработки")
                return ids

        except Exception as e:
            logger.error(f"Ошибка загрузки ID: {e}")
            return []

    def _load_already_fetched_ids(self) -> Set[str]:
        """Загружает ID уже обработанных автомобилей из JSONL файла"""
        file_path = DATA_DETAILS_DIR / self.output_file
        fetched_ids = set()

        if not file_path.exists():
            return fetched_ids

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        vehicle_id = data.get("id")
                        if vehicle_id:
                            fetched_ids.add(str(vehicle_id))

            logger.info(f"Найдено {len(fetched_ids)} уже обработанных ID")

        except Exception as e:
            logger.error(f"Ошибка загрузки уже обработанных ID: {e}")

        return fetched_ids

    def _extract_fields(self, details: dict, fields_map: dict) -> dict:
        """
        Извлекает только нужные поля из вложенного словаря API
        fields_map: {новое_имя: [путь, до, ключа]}
        """
        extracted = {}
        for key, path in fields_map.items():
            value = details
            try:
                for p in path:
                    value = value[p]

                # Handle special URL fields
                if key == "url":
                    extracted[key] = f"https://fem.encar.com/cars/detail/{value}"
                elif key == "diagnosis_report_url":
                    extracted[key] = (
                        f"https://fem.encar.com/cars/report/diagnosis/{value}"
                    )
                elif key == "inspection_report_url":
                    extracted[key] = (
                        f"https://fem.encar.com/cars/report/inspect/{value}"
                    )
                elif key == "accident_report_url":
                    extracted[key] = (
                        f"https://fem.encar.com/cars/report/accident/{value}"
                    )
                else:
                    extracted[key] = value
            except (KeyError, TypeError):
                extracted[key] = None
        return extracted

    def _save_vehicle_details_incremental(self, vehicle_id: str, details: dict):
        """Сохраняет детали автомобиля в JSON Lines файл"""
        file_path = DATA_DETAILS_DIR / self.output_file

        try:
            with open(file_path, "a", encoding="utf-8") as f:
                record = {"id": vehicle_id, "details": details}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Ошибка сохранения деталей для ID {vehicle_id}: {e}")

    def _parse_options(self, options_data: dict | None) -> dict:
        """Преобразует данные об опциях API в словарь True/False, проверяя только 'standard'"""
        result = {key: False for key in OPTIONS.keys()}
        if not options_data or "standard" not in options_data:
            return result

        standard_codes = set(options_data.get("standard", []))

        for name, code_str in OPTIONS.items():
            for code in code_str.split():
                if code in standard_codes:
                    result[name] = True
                    break

        return result

    def _check_accident_history_public(self, accident_url: str) -> dict:
        """
        Check accident history from public data (no login required)

        Args:
            accident_url: URL to the accident report page

        Returns:
            Dict with:
            - has_accident: bool
            - details: list of accident records with type, count, and cost
        """
        import re
        from playwright.sync_api import sync_playwright
        import time

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Load the accident report page
                page.goto(accident_url, wait_until="networkidle", timeout=30000)
                time.sleep(2)

                # Get page text
                page_text = page.evaluate("() => document.body.innerText")
                browser.close()

                # Pattern: "보험사고 이력 (타차 가해) 1회/303,770원" or "(내차 피해) 2회832,400원"
                # Pattern for own damage: 보험사고 이력 (내차 피해) X회Y원
                own_damage_pattern = (
                    r"보험사고\s*이력\s*\(내차\s*피해\)\s*(\d+)회\s*([\d,]+)원"
                )
                # Pattern for damage to others: 보험사고 이력 (타차 가해) X회/Y원
                others_damage_pattern = (
                    r"보험사고\s*이력\s*\(타차\s*가해\)\s*(\d+)회[/\s]*([\d,]+)원"
                )

                accident_details = []
                has_accident = False

                # Check for own damage accidents (my car was damaged - victim)
                own_matches = re.findall(own_damage_pattern, page_text)
                for match in own_matches:
                    count = int(match[0])
                    cost = match[1]
                    if count > 0:
                        has_accident = True
                        accident_details.append(
                            {
                                "accident_type": "Accidents Caused By Other Drivers",
                                "accident_count": count,
                                "total_cost": cost,
                            }
                        )

                # Check for damage to others accidents (I damaged another car - at fault)
                others_matches = re.findall(others_damage_pattern, page_text)
                for match in others_matches:
                    count = int(match[0])
                    cost = match[1]
                    if count > 0:
                        has_accident = True
                        accident_details.append(
                            {
                                "accident_type": "Accidents Caused By This Car's Owner",
                                "accident_count": count,
                                "total_cost": cost,
                            }
                        )

                return {"has_accident": has_accident, "details": accident_details}

        except Exception as e:
            logger.error(f"Error checking public accident data: {e}")
            return {"has_accident": None, "details": []}

    def fetch_details(
        self,
        vehicle_ids: Optional[List[str]] = None,
        skip_existing: bool = True,
        translate: bool = True,
        process_data: bool = True,
        apply_data_filters: bool = False,
    ):
        """
        Получает детальную информацию для списка автомобилей

        Args:
            vehicle_ids: Список ID автомобилей. Если None, загружает из файла
            skip_existing: Пропускать ли уже загруженные детали
            translate: Переводить ли корейские термины на английский
            process_data: Применять ли правила обработки данных
            apply_data_filters: Применять ли фильтры. None = из конфига
        """
        # Если ID не переданы, загружаем из файла
        if vehicle_ids is None:
            vehicle_ids = self._load_ids()

        if not vehicle_ids:
            logger.warning("Нет ID для обработки")
            return

        # Загружаем уже обработанные ID
        already_fetched = set()
        if skip_existing:
            already_fetched = self._load_already_fetched_ids()

        # Определяем, применять ли фильтры
        if apply_data_filters is None:
            apply_data_filters = FILTER_CONFIG.get("enabled", False)

        total = len(vehicle_ids)
        processed = 0
        skipped = 0
        errors = 0

        logger.info("=" * 60)
        logger.info(f"Начинаем получение деталей для {total} автомобилей")
        logger.info(f"Режим перевода: {'включен' if translate else 'выключен'}")
        logger.info(f"Обработка данных: {'включена' if process_data else 'выключена'}")
        logger.info(
            f"Фильтрация данных: {'включена' if apply_data_filters else 'выключена'}"
        )
        logger.info("=" * 60)

        for idx, vehicle_id in enumerate(vehicle_ids, 1):
            # Пропускаем уже обработанные
            if skip_existing and vehicle_id in already_fetched:
                skipped += 1
                if skipped % 100 == 0:
                    logger.info(
                        f"[{idx}/{total}] Пропущено {skipped} уже обработанных ID"
                    )
                continue

            logger.info(f"[{idx}/{total}] Получаем детали для ID: {vehicle_id}")

            # Получаем детали
            details = self.client.get_vehicle_details(vehicle_id)

            if details:
                # Извлекаем только нужные поля
                filtered_details = self._extract_fields(details, FIELDS_TO_EXTRACT)

                filtered_details["options"] = self._parse_options(
                    details.get("options")
                )

                # Check accident history from public data (no login required)
                if self.check_history and filtered_details.get("accident_report_url"):
                    logger.info(f"[{idx}/{total}] 🔍 Checking accident history...")
                    try:
                        accident_info = self._check_accident_history_public(
                            filtered_details["accident_report_url"]
                        )
                        filtered_details["has_accident_history"] = accident_info[
                            "has_accident"
                        ]
                        filtered_details["accident_details"] = accident_info["details"]
                    except Exception as e:
                        logger.error(
                            f"Error checking accident history for {vehicle_id}: {e}"
                        )
                        filtered_details["has_accident_history"] = None
                        filtered_details["accident_details"] = []
                else:
                    filtered_details["has_accident_history"] = None
                    filtered_details["accident_details"] = []

                # 1. Обрабатываем данные (очистка, форматирование)
                if process_data:
                    filtered_details = self.processor.process_dict(filtered_details)

                # 2. Переводим
                if translate:
                    filtered_details = self.translator.translate_dict(filtered_details)

                # 3. Применяем фильтры
                self.filter_stats["total_processed"] += 1
                if apply_data_filters:
                    if not apply_filters(filtered_details, FILTER_CONFIG):
                        self.filter_stats["filtered_out"] += 1
                        logger.info(f"[{idx}/{total}] ⊘ ID {vehicle_id} отфильтрован")
                        continue

                filtered_details["parsed_at"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                # 4. Сохраняем
                self._save_vehicle_details_incremental(vehicle_id, filtered_details)
                processed += 1

                if processed % 10 == 0:
                    logger.info(
                        f"Обработано {processed}/{total - skipped} новых записей"
                    )

            else:
                errors += 1
                logger.error(
                    f"[{idx}/{total}] ✗ Ошибка получения деталей для ID: {vehicle_id}"
                )

        # Итоговая статистика
        logger.info("=" * 60)
        logger.info("✅ ОБРАБОТКА ЗАВЕРШЕНА")
        logger.info("=" * 60)
        logger.info(f"  Всего ID: {total}")
        logger.info(f"  Обработано и сохранено: {processed}")
        logger.info(f"  Пропущено (уже есть): {skipped}")
        logger.info(f"  Отфильтровано: {self.filter_stats['filtered_out']}")
        logger.info(f"  Ошибок: {errors}")
        logger.info("=" * 60)

        # Статистика переводов
        if translate:
            self.translator.print_statistics()

        # Статистика обработки данных
        if process_data:
            self.processor.print_statistics()

    def fetch_single_car_details(
        self,
        vehicle_id: str,
        translate: bool = True,
        process_data: bool = True,
    ):
        logger.info(f"Получаем детали для ID: {vehicle_id}")

        details = self.client.get_vehicle_details(vehicle_id)

        if details:
            filtered_details = self._extract_fields(details, SMALL_FIELDS_TO_EXTRACT)

            if process_data:
                filtered_details = self.processor.process_dict(filtered_details)

            if translate:
                filtered_details = self.translator.translate_dict(filtered_details)

            filtered_details["parsed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            logger.info(f"ID {vehicle_id} успешно обработан")

            return filtered_details
        else:
            logger.error(f"Ошибка получения деталей для ID: {vehicle_id}")

    def close(self):
        """Закрывает соединения"""
        self.client.close()
