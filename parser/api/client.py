"""
API клиент для взаимодействия с Encar.com API
"""

import json
import time
import random
from typing import Dict, Optional
import requests

from logger.logging import get_parser_logger

from config.paths import PARSER_COOKIES_DIR

from parser.config.config import (
    API_BASE_URL,
    API_LIST_ENDPOINT,
    API_VEHICLE_DETAIL_ENDPOINT,
    DELAY_BETWEEN_REQUESTS,
    DELAY_RANDOMIZATION,
    REQUEST_TIMEOUT,
    RETRY_ATTEMPTS,
)

logger = get_parser_logger(__name__)


class EncarAPIClient:
    """Клиент для работы с Encar API"""

    def __init__(self, headers_file: str = f"{PARSER_COOKIES_DIR}/headers.json"):
        self.session = requests.Session()

        try:
            with open(headers_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Устанавливаем cookies в сессию
            for c in data.get("cookies", []):
                name = c.get("name")
                value = c.get("value")
                if not name or value is None:
                    continue
                self.session.cookies.set(
                    name=name,
                    value=value,
                    domain=c.get("domain"),
                    path=c.get("path", "/"),
                )

            # Устанавливаем User-Agent из файла
            ua = data.get("user_agent")
            if ua:
                self.session.headers.update({"User-Agent": ua})

            # Остальные стандартные заголовки
            self.session.headers.update(
                {
                    "Accept": "application/json",
                    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Referer": "https://www.encar.com/",
                    "Origin": "https://www.encar.com",
                    "X-Requested-With": "XMLHttpRequest",
                }
            )

            logger.info(f"Cookies и UA успешно загружены из {headers_file}")

        except FileNotFoundError:
            logger.warning(
                f"{headers_file} не найден, соберите необходимые Cookies и UA."
            )

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Выполняет HTTP запрос с повторными попытками при ошибках.
        Перед запросом убеждаемся, что есть cookies от браузера.

        Args:
            url: URL для запроса
            params: GET параметры

        Returns:
            Dict с JSON ответом или None при ошибке
        """

        for attempt in range(RETRY_ATTEMPTS):
            try:
                logger.info(f"Запрос: {url} (попытка {attempt + 1}/{RETRY_ATTEMPTS})")

                response = self.session.get(
                    url, params=params, timeout=(10, REQUEST_TIMEOUT)
                )
                response.raise_for_status()

                # Проверка на корректность JSON
                json_data = response.json()

                # Проверка на блокировку/капчу
                if isinstance(json_data, dict) and json_data.get("error"):
                    logger.error(f"API вернул ошибку: {json_data.get('error')}")
                    return None

                # Добавляем случайную задержку между запросами
                self._apply_delay()

                return json_data

            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                logger.error(f"Ответ сервера: {response.text[:200]}")
                return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка запроса (попытка {attempt + 1}): {e}")

                if attempt < RETRY_ATTEMPTS - 1:
                    wait_time = 2**attempt  # Экспоненциальная задержка
                    logger.info(f"Повтор через {wait_time} секунд...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Все попытки исчерпаны для URL: {url}")
                    return None

    def _apply_delay(self):
        """Применяет случайную задержку между запросами для избежания блокировки"""
        delay = DELAY_BETWEEN_REQUESTS + random.uniform(0, DELAY_RANDOMIZATION)
        time.sleep(delay)

    def get_car_list(
        self,
        sell_type: str,
        brand: str,
        model: str,
        start: int,
        count: int,
        year_from: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Получает список автомобилей

        Args:
            sell_type: Тип продажи
            brand: Бренд автомобиля
            model: Модель автомобиля
            start: Начальная позиция
            count: Количество результатов
            year_from: Минимальный год выпуска (опционально)

        Returns:
            Dict с результатами или None
        """
        url = f"{API_BASE_URL}{API_LIST_ENDPOINT}"

        # Формируем query параметр
        query = f"And.Hidden.N._.CarType.A._.Manufacturer.{brand}."

        # Добавляем ModelGroup только если модель указана
        if model:
            query += f"_.ModelGroup.{model}."

        # Добавляем фильтр по году если указан (до SellType)
        if year_from:
            query += f"_.FormYear.{year_from}-."

        query += f"_.SellType.{sell_type}."

        sr = f"|MileageAsc|{start}|{count}"

        params = {"count": "true", "q": query, "sr": sr}

        return self._make_request(url, params)

    def get_vehicle_details(self, vehicle_id: str) -> Optional[Dict]:
        """
        Получает детальную информацию об автомобиле

        Args:
            vehicle_id: ID автомобиля

        Returns:
            Dict с деталями автомобиля или None
        """
        url = f"{API_BASE_URL}{API_VEHICLE_DETAIL_ENDPOINT.format(id=vehicle_id)}"
        return self._make_request(url)

    def close(self):
        """Закрывает сессию"""
        self.session.close()
