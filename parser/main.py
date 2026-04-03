"""
Главный файл для запуска парсера Encar.com
"""

import sys
import asyncio

# CRITICAL: Set Windows event loop policy BEFORE any other imports
# Python 3.11+ on Windows defaults to ProactorEventLoop, which breaks Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Also force create a fresh SelectorEventLoop (in case ProactorEventLoop was already instantiated)
    asyncio.set_event_loop(asyncio.SelectorEventLoop())

import argparse
import platform
import io
from typing import List, Optional

# Windows UTF-8 encoding fix for emoji output (only wrap if not already done)
if sys.platform.startswith("win") and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        # Already wrapped or no buffer available
        pass

from logger.logging import get_parser_logger
from parser.collectors.details_fetcher import VehicleDetailsFetcher
from parser.collectors.id_collector import CarIDCollector


logger = get_parser_logger(__name__)


def collect_ids(append: bool = False):
    logger.info("=" * 60)
    """
    Собирает ID автомобилей

    Args:
        append: Добавлять к существующим ID или перезаписать
    """
    logger.info("🚗 ЭТАП 1: Сбор ID автомобилей")
    logger.info("=" * 60)

    collector = CarIDCollector()
    try:
        ids = collector.collect_all_ids(append_mode=append)
        logger.info(f"✅ Собрано {len(ids)} уникальных ID")
        return ids
    finally:
        collector.close()


def fetch_details(
    vehicle_ids: Optional[List[str]] = None,
    skip_existing: bool = True,
    translate: bool = True,
    process_data: bool = True,
    apply_filters: bool = False,
    check_history: bool = True,
):
    """
    Получает детальную информацию об автомобилях

    Args:
        vehicle_ids: Список ID автомобилей для обработки (опционально)
        skip_existing: Пропускать уже загруженные детали
        translate: Переводить корейские термины
        process_data: Применять правила обработки данных
        apply_filters: Применять фильтры данных
        check_history: Проверять историю аварий
    """
    logger.info("=" * 60)
    logger.info("📝 ЭТАП 2: Получение деталей автомобилей")
    logger.info("=" * 60)

    fetcher = VehicleDetailsFetcher(check_history=check_history)
    try:
        fetcher.fetch_details(
            vehicle_ids=vehicle_ids,
            skip_existing=skip_existing,
            translate=translate,
            process_data=process_data,
            apply_data_filters=apply_filters,
        )
    finally:
        fetcher.close()


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Парсер данных с Encar.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  Полный цикл (сбор + получение деталей):
    python main.py --mode full

  Полный цикл с множественными моделями:
    python main.py --mode full --multi-models
    
  Полный цикл с множественными брендами:
    python main.py --mode full --multi-brands

  Сбор ID для одной модели (из SEARCH_PARAMS):
    python main.py --mode collect

  Только получение деталей:
    python main.py --mode fetch

  Получение с переводом и обработкой:
    python main.py --mode fetch --translate --process

  Получение без перевода:
    python main.py --mode fetch --no-translate

  Получение с фильтрацией:
    python main.py --mode fetch --filter
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["collect", "fetch", "full"],
        default="full",
        help="Режим работы",
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help="Добавлять новые ID к существующим (только для collect)",
    )

    parser.add_argument(
        "--redownload",
        action="store_true",
        help="Перезагрузить существующие детали (только для fetch)",
    )

    parser.add_argument(
        "--translate",
        action="store_true",
        default=True,
        help="Переводить корейские термины на английский (по умолчанию включено)",
    )

    parser.add_argument("--no-translate", action="store_true", help="Отключить перевод")

    parser.add_argument(
        "--process",
        action="store_true",
        default=True,
        help="Применять правила обработки данных (по умолчанию включено)",
    )

    parser.add_argument(
        "--no-process", action="store_true", help="Отключить обработку данных"
    )

    parser.add_argument(
        "--filter",
        action="store_true",
        help="Применять фильтры данных (см. rules.py)",
    )

    parser.add_argument(
        "--no-check-history",
        action="store_true",
        help="Отключить проверку истории аварий",
    )

    parser.add_argument(
        "--ids",
        nargs="+",
        help="Список ID автомобилей для обработки (например: --ids 41546857 38118271)",
    )

    args = parser.parse_args()

    # Определяем настройки перевода и обработки
    translate = not args.no_translate if args.no_translate else args.translate
    process_data = not args.no_process if args.no_process else args.process
    check_history = not args.no_check_history

    try:
        if args.mode == "collect":
            collect_ids(append=args.append)

        elif args.mode == "fetch":
            fetch_details(
                vehicle_ids=args.ids,
                skip_existing=not args.redownload,
                translate=translate,
                process_data=process_data,
                apply_filters=args.filter,
                check_history=check_history,
            )

        elif args.mode == "full":
            # Полный цикл
            collect_ids(append=args.append)
            fetch_details(
                vehicle_ids=args.ids,
                skip_existing=not args.redownload,
                translate=translate,
                process_data=process_data,
                apply_filters=args.filter,
                check_history=check_history,
            )

        logger.info("=" * 60)
        logger.info("🎉 РАБОТА ЗАВЕРШЕНА УСПЕШНО!")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Остановлено пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)


if __name__ == "__main__":
    main()
