# 🚗 Encar Parser & Telegram Bot

Комплексное решение для парсинга автомобилей с корейского сайта [Encar.com](https://www.encar.com) и взаимодействия через Telegram-бота.

## 📋 Содержание

- [Возможности](#-возможности)
- [Архитектура проекта](#-архитектура-проекта)
- [Установка](#-установка)
- [Конфигурация](#-конфигурация)
- [Использование](#-использование)
  - [Парсер](#парсер)
  - [Telegram Bot](#telegram-bot)
- [Документация модулей](#-документация-модулей)
- [Troubleshooting](#-troubleshooting)
- [Разработка](#-разработка)

---

## 🎯 Возможности

### Парсер
- ✅ Сбор ID автомобилей по заданным брендам и моделям
- ✅ Получение детальной информации о каждом автомобиле
- ✅ Автоматический перевод корейских терминов на английский
- ✅ Обработка и фильтрация данных по настраиваемым правилам
- ✅ Продвинутая защита от детекции (Canvas, WebGL, Audio fingerprinting)
- ✅ Инкрементальное сохранение в JSONL формате
- ✅ Поддержка возобновления работы после остановки

### Telegram Bot
- ✅ Получение информации по ссылке на автомобиль
- ✅ Парсинг в реальном времени
- ✅ Отправка фотографий галереей (до 10 изображений)
- ✅ Форматированный вывод характеристик

---

## 🏗 Архитектура проекта

```
.
├── bot/                          # Telegram бот
│   ├── handlers/                 # Обработчики команд
│   │   ├── common.py            # Общие команды (/start, /help)
│   │   └── parser.py            # Парсинг по ссылке
│   ├── config/
│   │   └── settings.py          # Настройки бота
│   └── states/
│       └── parser.py            # FSM состояния
│
├── parser/                       # Парсер Encar.com
│   ├── api/
│   │   └── client.py            # HTTP клиент для Encar API
│   ├── collectors/
│   │   ├── id_collector.py      # Сбор ID автомобилей
│   │   └── details_fetcher.py   # Получение детальной информации
│   ├── processing/
│   │   ├── processor.py         # Обработка данных
│   │   └── rules.py             # Правила обработки и фильтрации
│   ├── translation/
│   │   ├── cache.py             # Кеш переводов
│   │   ├── translator.py        # Переводчик KO -> EN
│   │   └── missing.json         # Непереведенные термины
│   ├── scripts/
│   │   ├── fetch_cookies.py     # Получение cookies (undetected)
│   │   ├── run_fetch_cookies.sh # Wrapper для Xvfb
│   │   └── cookies/
│   │       └── headers.json     # Cookies и fingerprint
│   ├── config/
│   │   └── config.py            # Конфигурация парсера
│   └── main.py                  # Точка входа парсера
│
├── config/                       # Общая конфигурация
│   ├── paths.py                 # Пути проекта
│   └── settings.py              # Базовые настройки
│
├── logger/                       # Система логирования
│   └── logging.py               # Централизованный логгер
│
├── data/                         # Данные (создается автоматически)
│   ├── car_ids_YYYYMMDD_HHMMSS.json      # Собранные ID (с timestamp)
│   ├── duplicated_ids_YYYYMMDD_HHMMSS.json  # Дубликаты (с timestamp)
│   └── details/
│       └── cars_data_YYYYMMDD_HHMMSS.jsonl  # Детали автомобилей (с timestamp)
│
├── logs/                         # Логи (создается автоматически)
│   ├── parser.log
│   └── bot.log
│
├── .env.example                  # Пример переменных окружения
├── requirements.txt              # Python зависимости
└── README.md                     # Этот файл
```

---

## 🚀 Использование

### Парсер

#### Полный цикл (сбор ID + детали)

```bash
python -m parser.main --mode full
```

#### Только сбор ID

```bash
python -m parser.main --mode collect
```

#### Только получение деталей

```bash
python -m parser.main --mode fetch
```

#### Продвинутые опции

```bash
# Без перевода
python -m parser.main --mode fetch --no-translate

# С фильтрацией (см. rules.py)
python -m parser.main --mode fetch --filter

# Перезагрузить существующие детали
python -m parser.main --mode fetch --redownload

# Добавить новые ID к существующим
python -m parser.main --mode collect --append
```

### Telegram Bot

```bash
python -m bot.bot
```

Бот поддерживает команды:
- `/start` - Начать работу
- `/help` - Справка
- `/cancel` - Отменить текущую операцию

Отправьте ссылку на автомобиль:
```
https://fem.encar.com/cars/detail/40647630?carid=40647630
```

---

## 📚 Документация модулей

### Parser API Client (`parser/api/client.py`)

```python
from parser.api.client import EncarAPIClient

client = EncarAPIClient()

# Получить список автомобилей
data = client.get_car_list(
    sell_type="일반",
    brand="현대",
    model="소나타",
    start=0,
    count=100
)

# Получить детали автомобиля
details = client.get_vehicle_details("40647630")

client.close()
```

### Translator (`parser/translation/translator.py`)

```python
from parser.translation.translator import Translator

translator = Translator()

# Перевести текст
translated = translator.translate("가솔린", field_name="fuel")
# Результат: "Gasoline"

# Перевести весь словарь
data = {"fuel": "디젤", "color": "흰색"}
translated_data = translator.translate_dict(data)
# Результат: {"fuel": "Diesel", "color": "White"}

# Статистика
translator.print_statistics()
```

### Data Processor (`parser/processing/processor.py`)

```python
from parser.processing.processor import DataProcessor
from parser.processing.rules import CUSTOM_PROCESSING_RULES

processor = DataProcessor(processing_rules=CUSTOM_PROCESSING_RULES)

# Обработать данные
data = {
    "price": "25000000",
    "mileage": "50000",
    "region": "경기 수원시 권선구"
}

processed = processor.process_dict(data)
# Результат: {"price": 25000000, "mileage": 50000, "region": "경기"}
```

### Кастомные правила обработки

Добавьте свои правила в `parser/processing/rules.py`:

```python
def process_custom_field(value: Any) -> Optional[str]:
    """Ваша логика обработки"""
    return value.upper()

CUSTOM_PROCESSING_RULES = {
    "my_field": process_custom_field,
    # ... другие правила
}
```

### Фильтрация данных

Настройте фильтры в `parser/processing/rules.py`:

```python
FILTER_CONFIG = {
    "enabled": True,
    "min_year": 2020,           # Минимальный год
    "max_mileage": 100000,      # Максимальный пробег (км)
    "min_price": 5000000,       # Минимальная цена (₩)
    "allowed_brands": ["Hyundai", "Kia"],  # Только эти бренды
    "allowed_fuels": ["Gasoline", "Diesel"],
}
```

---

## 📊 Формат данных

### Сохраненные детали (`data/details/cars_data_YYYYMMDD_HHMMSS.jsonl`)

```json
{
  "id": "40647630",
  "details": {
    "id": "40647630",
    "vin": "KMHXX00XXXX000000",
    "vehnumber": "12가3456",
    "brand": "Hyundai",
    "model": "Sonata",
    "year": 2023,
    "mileage": 15000,
    "fuel": "Gasoline",
    "transmission": "Automatic",
    "color": "White",
    "price": 25000000,
    "region": "Gyeonggi",
    "images": ["https://...", "https://..."],
    "options": {
      "sunroof": true,
      "navigation": true
    },
    "parsed_at": "2025-01-26 12:00:00"
  }
}
```

---

## 🛡️ Безопасность

### Защита от детекции

Проект использует продвинутые техники обхода:
- **Canvas Fingerprint Spoofing** - уникальный шум для каждой сессии
- **WebGL Masking** - подмена vendor/renderer
- **Audio Context Spoofing** - искажение аудио fingerprint
- **Timing Attack Protection** - шум в `performance.now()`
- **Battery API Spoofing** - реалистичные значения
- **Network Info Masking** - имитация 4G/WiFi

**⚠️ Disclaimer:** Используйте этот инструмент ответственно и в соответствии с законодательством вашей страны и правилами целевого веб-сайта.
