"""
Модуль для получения детальной информации об автомобилях
"""

import json
import time
import random
from datetime import datetime
from typing import List, Optional, Set

from logger.logging import get_parser_logger
from config.paths import DATA_DETAILS_DIR, IDS_FILE, get_timestamped_filename

from parser.api.client import EncarAPIClient
from parser.config.config import (
    FIELDS_TO_EXTRACT,
    SMALL_FIELDS_TO_EXTRACT,
    OPTIONS,
    ACCIDENT_CHECK_DELAY,
    DELAY_RANDOMIZATION,
    BROWSER_RESTART_INTERVAL,
)
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

        # Browser instance for accident history checking (reusable)
        self.playwright = None
        self.browser = None
        self.browser_page = None
        self.browser_check_counter = (
            0  # Track cars processed since last browser restart
        )
        self.next_restart_at = random.randint(
            BROWSER_RESTART_INTERVAL - 10, BROWSER_RESTART_INTERVAL + 10
        )  # Random restart interval (90-110 cars)
        if check_history:
            self._init_browser()

        # Статистика фильтрации
        self.filter_stats = {
            "total_processed": 0,
            "filtered_out": 0,
        }

        self.accident_retry_ids = []  # IDs that need accident recheck
        self.scrape_retry_ids = []  # IDs that failed to scrape

    def _ensure_details_dir(self):
        """Создает директорию для деталей если её нет"""
        DATA_DETAILS_DIR.mkdir(parents=True, exist_ok=True)

    def _init_browser(self):
        """
        Initialize ONE browser instance + ONE tab for reuse across ALL cars.
        Much faster than creating new browser/tab for each car.
        This single tab will be reused for all 19,511+ accident checks.
        """
        try:
            from playwright.sync_api import sync_playwright

            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )
            self.browser_page = self.browser.new_page()
            logger.info(
                "🌐 Browser initialized with ONE reusable tab for all accident checks"
            )
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            self.playwright = None
            self.browser = None
            self.browser_page = None

    def _restart_browser(self):
        """
        Restart browser to simulate human behavior (taking breaks, new sessions).
        Called at random intervals (90-110 cars) to look more natural.
        """
        try:
            logger.info(
                f"🔄 Restarting browser after {self.browser_check_counter} cars (session break)..."
            )

            # Close existing browser
            if self.browser_page:
                self.browser_page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            # Reset counter and set new random restart target
            self.browser_check_counter = 0
            self.next_restart_at = random.randint(
                BROWSER_RESTART_INTERVAL - 10, BROWSER_RESTART_INTERVAL + 10
            )
            logger.info(f"⏱️ Next restart scheduled in ~{self.next_restart_at} cars")

            # Small pause to simulate break (2-5 seconds)
            time.sleep(random.uniform(2, 5))

            # Initialize new browser
            self._init_browser()
            logger.info("✅ Browser restarted successfully")
        except Exception as e:
            logger.error(f"Error restarting browser: {e}")
            # Try to reinitialize
            self._init_browser()

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

    def _check_accident_history_public(self, accident_url: str, vehicle_id: str = None) -> dict:
        import re

        result = {"has_accident": None, "details": []}

        if not self.browser_page:
            logger.warning(f"⚠️ Browser not initialized for {vehicle_id}, queueing for retry")
            if vehicle_id:
                self.accident_retry_ids.append(vehicle_id)
            return result

        try:
            page = self.browser_page
            page.set_default_timeout(12000)  # 12 second timeout built into Playwright
            
            page.goto(accident_url, wait_until="load", timeout=10000)
            page.wait_for_selector("body", timeout=3000)
            page_text = page.evaluate("() => document.body.innerText")

            own_damage_pattern = r"보험사고\s*이력\s*\(내차\s*피해\)\s*(\d+)회\s*([\d,]+)원"
            others_damage_pattern = r"보험사고\s*이력\s*\(타차\s*가해\)\s*(\d+)회[/\s]*([\d,]+)원"

            has_accident = False
            accident_details = []

            for match in re.findall(own_damage_pattern, page_text):
                count = int(match[0])
                if count > 0:
                    has_accident = True
                    accident_details.append({
                        "accident_type": "Accidents Caused By Other Drivers",
                        "accident_count": count,
                        "total_cost": match[1],
                    })

            for match in re.findall(others_damage_pattern, page_text):
                count = int(match[0])
                if count > 0:
                    has_accident = True
                    accident_details.append({
                        "accident_type": "Accidents Caused By This Car's Owner",
                        "accident_count": count,
                        "total_cost": match[1],
                    })

            result["has_accident"] = has_accident
            result["details"] = accident_details
            logger.info(f"✅ Accident check successful for {vehicle_id}: has_accident={has_accident}")

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"⚠️ Accident check failed for {vehicle_id}: {error_msg}")
            
            # ALWAYS queue for retry if check failed - ensure no car is left behind
            if vehicle_id and vehicle_id not in self.accident_retry_ids:
                self.accident_retry_ids.append(vehicle_id)
                logger.info(f"📋 Queued {vehicle_id} for retry (total queued: {len(self.accident_retry_ids)})")
            
            # If browser is in bad state, restart it
            if "browser" in error_msg.lower() or "closed" in error_msg.lower():
                logger.info("🔄 Restarting browser due to browser error")
                try:
                    self._restart_browser()
                except Exception as restart_err:
                    logger.error(f"Failed to restart browser: {restart_err}")

        return result

    def _retry_failed_accident_checks(self):
        """
        Retry accident history checks that previously failed.
        Keep retrying until all cars have accident data (or are truly unreachable).
        """
        if not self.accident_retry_ids:
            logger.info("✅ All cars successfully processed - no retries needed")
            return

        logger.info("=" * 70)
        logger.info(f"🔄 RETRY PHASE: Attempting to complete accident checks for {len(self.accident_retry_ids)} cars")
        logger.info("=" * 70)

        file_path = DATA_DETAILS_DIR / self.output_file
        max_retry_attempts = 3
        retry_attempt = 0
        cars_to_retry = self.accident_retry_ids.copy()

        while cars_to_retry and retry_attempt < max_retry_attempts:
            retry_attempt += 1
            logger.info(f"🔄 Retry attempt {retry_attempt}/{max_retry_attempts}")
            
            still_failing = []

            for vehicle_id in cars_to_retry:
                logger.info(f"🔄 Retrying car ID: {vehicle_id}")

                # Read the already-saved record
                lines = []
                target_line_idx = None
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f):
                            lines.append(line)
                            if line.strip():
                                data = json.loads(line)
                                if str(data.get("id")) == str(vehicle_id):
                                    target_line_idx = i
                except Exception as e:
                    logger.error(f"Error reading file for retry: {e}")
                    still_failing.append(vehicle_id)
                    continue

                if target_line_idx is None:
                    logger.warning(f"ID {vehicle_id} not found in output file")
                    still_failing.append(vehicle_id)
                    continue

                # Get the accident URL from the saved record
                try:
                    saved_record = json.loads(lines[target_line_idx])
                    accident_url = saved_record.get("details", {}).get("accident_report_url")

                    if not accident_url:
                        logger.warning(f"No accident URL for ID {vehicle_id}")
                        still_failing.append(vehicle_id)
                        continue

                    # Retry the check
                    logger.info(f"   Checking accident URL: {accident_url}")
                    accident_info = self._check_accident_history_public(accident_url, vehicle_id=None)

                    if accident_info["has_accident"] is None:
                        logger.warning(f"⚠️ Retry still failed for ID {vehicle_id}")
                        still_failing.append(vehicle_id)
                        continue

                    # Update the record with accident data
                    saved_record["details"]["has_accident_history"] = accident_info["has_accident"]
                    saved_record["details"]["accident_details"] = accident_info["details"]
                    lines[target_line_idx] = json.dumps(saved_record, ensure_ascii=False) + "\n"

                    # Rewrite the file with updated record
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    logger.info(f"✅ Accident data SAVED for ID {vehicle_id}: has_accident={accident_info['has_accident']}")

                except Exception as e:
                    logger.error(f"Error processing retry for ID {vehicle_id}: {e}")
                    still_failing.append(vehicle_id)

            cars_to_retry = still_failing
            
            if cars_to_retry:
                logger.info(f"⏳ {len(cars_to_retry)} cars still failing, resting before retry...")
                time.sleep(5)  # Brief rest between retry attempts

        # Final report
        logger.info("=" * 70)
        if cars_to_retry:
            logger.warning(f"⚠️ {len(cars_to_retry)} cars could not get accident history after {max_retry_attempts} attempts:")
            for vid in cars_to_retry:
                logger.warning(f"   - ID {vid}")
        else:
            logger.info(f"✅ All {len(self.accident_retry_ids)} cars successfully retried!")
        logger.info("=" * 70)

        self.accident_retry_ids.clear()

    def _retry_failed_scrapes(
        self,
        translate: bool = True,
        process_data: bool = True,
        apply_data_filters: bool = False,
        max_retry_attempts: int = 2,
    ):
        """
        Retries fetching details for cars that failed during the initial scrape phase
        
        Args:
            translate: Whether to translate korean terms
            process_data: Whether to apply data processing rules
            apply_data_filters: Whether to apply filters
            max_retry_attempts: Number of retry attempts (default 2)
        """
        if not self.scrape_retry_ids:
            return

        logger.info("=" * 70)
        logger.info(f"🔄 RETRYING {len(self.scrape_retry_ids)} FAILED SCRAPES")
        logger.info("=" * 70)

        cars_to_retry = self.scrape_retry_ids.copy()
        retry_attempt = 0
        successfully_retried = 0

        while cars_to_retry and retry_attempt < max_retry_attempts:
            retry_attempt += 1
            logger.info(f"🔄 Retry attempt {retry_attempt}/{max_retry_attempts} for {len(cars_to_retry)} cars")

            still_failing = []

            for vehicle_id in cars_to_retry:
                try:
                    logger.info(f"🔄 Retrying car ID: {vehicle_id}")

                    # Try to fetch details again
                    details = self.client.get_vehicle_details(vehicle_id)

                    if not details:
                        logger.warning(f"⚠️ Still failed to fetch details for ID {vehicle_id}")
                        still_failing.append(vehicle_id)
                        continue

                    # Extract fields
                    filtered_details = self._extract_fields(details, FIELDS_TO_EXTRACT)
                    filtered_details["options"] = self._parse_options(
                        details.get("options")
                    )

                    # Check accident history
                    if self.check_history and filtered_details.get("accident_report_url"):
                        try:
                            accident_info = self._check_accident_history_public(
                                filtered_details["accident_report_url"],
                                vehicle_id=vehicle_id,
                            )
                            filtered_details["has_accident_history"] = accident_info[
                                "has_accident"
                            ]
                            filtered_details["accident_details"] = accident_info["details"]
                        except Exception as e:
                            logger.error(
                                f"Error checking accident history on retry for {vehicle_id}: {e}"
                            )
                            filtered_details["has_accident_history"] = None
                            filtered_details["accident_details"] = []
                    else:
                        filtered_details["has_accident_history"] = None
                        filtered_details["accident_details"] = []

                    # Process data
                    if process_data:
                        filtered_details = self.processor.process_dict(filtered_details)

                    # Translate
                    if translate:
                        filtered_details = self.translator.translate_dict(filtered_details)

                    # Apply filters
                    if apply_data_filters:
                        if not apply_filters(filtered_details, FILTER_CONFIG):
                            logger.info(f"⊘ ID {vehicle_id} filtered out on retry")
                            successfully_retried += 1
                            continue

                    # Save the vehicle details
                    filtered_details["parsed_at"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    self._save_vehicle_details_incremental(vehicle_id, filtered_details)
                    logger.info(f"✅ Successfully retried and saved ID {vehicle_id}")
                    successfully_retried += 1

                except Exception as e:
                    logger.error(f"Error retrying car ID {vehicle_id}: {e}")
                    still_failing.append(vehicle_id)

            cars_to_retry = still_failing

            if cars_to_retry:
                logger.info(
                    f"⏳ {len(cars_to_retry)} cars still failing, resting before retry..."
                )
                time.sleep(5)  # Brief rest between retry attempts

        # Final report
        logger.info("=" * 70)
        logger.info(
            f"✅ Retry complete: {successfully_retried} cars successfully retried"
        )
        if cars_to_retry:
            logger.warning(
                f"⚠️ {len(cars_to_retry)} cars could not be scraped after {max_retry_attempts} attempts:"
            )
            for vid in cars_to_retry:
                logger.warning(f"   - ID {vid}")
        logger.info("=" * 70)

        self.scrape_retry_ids.clear()

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
            try:
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
                                filtered_details["accident_report_url"],
                                vehicle_id=vehicle_id,
                            )
                            filtered_details["has_accident_history"] = accident_info[
                                "has_accident"
                            ]
                            filtered_details["accident_details"] = accident_info["details"]

                            # Increment browser counter
                            self.browser_check_counter += 1

                            # Restart browser at random intervals (90-110 cars) to look more human
                            if self.browser_check_counter >= self.next_restart_at:
                                self._restart_browser()

                            # Добавляем дополнительную случайную задержку после проверки аварий
                            delay = ACCIDENT_CHECK_DELAY + random.uniform(
                                0, DELAY_RANDOMIZATION
                            )
                            time.sleep(delay)
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
                    # Add to retry list for potential rescrap at the end
                    if vehicle_id not in self.scrape_retry_ids:
                        self.scrape_retry_ids.append(vehicle_id)

            except Exception as e:
                errors += 1
                logger.error(
                    f"[{idx}/{total}] ✗ Исключение при обработке ID {vehicle_id}: {e}",
                    exc_info=True
                )
                # Add to retry list for potential rescrap at the end
                if vehicle_id not in self.scrape_retry_ids:
                    self.scrape_retry_ids.append(vehicle_id)

        # Retry any cars where accident check timed out
        if self.accident_retry_ids:
            self._retry_failed_accident_checks()

        # Retry any cars that failed to scrape during initial pass
        if self.scrape_retry_ids:
            self._retry_failed_scrapes(
                translate=translate,
                process_data=process_data,
                apply_data_filters=apply_data_filters,
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

        # Close browser instance if it was initialized
        if self.browser_page:
            self.browser_page.close()
            logger.info("🌐 Browser page closed")
        if self.browser:
            self.browser.close()
            logger.info("🌐 Browser closed")
        if self.playwright:
            self.playwright.stop()
            logger.info("🌐 Playwright stopped")
