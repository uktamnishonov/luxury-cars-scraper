#!/bin/bash

# ============================================
# Wrapper для запуска fetch_cookies.py через Xvfb
# Создает виртуальный дисплей для браузера
# ============================================

set -e  # Останавливаться при ошибках

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🖥️  Xvfb Cookie Fetcher Wrapper"
echo "=========================================="

# Проверяем наличие Xvfb
if ! command -v Xvfb &> /dev/null; then
    echo -e "${RED}❌ Xvfb не установлен!${NC}"
    echo ""
    echo "Установите командой:"
    echo "  sudo apt-get install -y xvfb x11-utils xfonts-100dpi xfonts-75dpi xfonts-scalable"
    exit 1
fi

# Проверяем наличие Python скрипта
if [ ! -f "fetch_cookies.py" ]; then
    echo -e "${RED}❌ fetch_cookies.py не найден в текущей директории!${NC}"
    exit 1
fi

# Параметры виртуального дисплея
SCREEN_WIDTH=1920
SCREEN_HEIGHT=1080
SCREEN_DEPTH=24
DISPLAY_NUM=99

echo -e "${GREEN}✅ Xvfb найден: $(which Xvfb)${NC}"
echo "📐 Настройки дисплея: ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}"
echo ""

# Функция для очистки при выходе
cleanup() {
    echo ""
    echo "🧹 Очистка..."
    if [ ! -z "$XVFB_PID" ]; then
        kill $XVFB_PID 2>/dev/null || true
        echo "✅ Xvfb процесс остановлен"
    fi
}

trap cleanup EXIT INT TERM

# Запускаем Xvfb в фоне
echo "🚀 Запуск виртуального дисплея..."
Xvfb :${DISPLAY_NUM} -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH} -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Ждем запуска Xvfb
sleep 2

# Проверяем что Xvfb запустился
if ! ps -p $XVFB_PID > /dev/null; then
    echo -e "${RED}❌ Не удалось запустить Xvfb!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Xvfb запущен (PID: $XVFB_PID, DISPLAY: :${DISPLAY_NUM})${NC}"
echo ""

# Устанавливаем переменную окружения DISPLAY
export DISPLAY=:${DISPLAY_NUM}

# Запускаем Python скрипт с переданными аргументами
echo "🐍 Запуск fetch_cookies.py..."
echo "=========================================="
echo ""

# Передаем все аргументы в Python скрипт
python -m parser.scripts.fetch_cookies "$@"
EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Скрипт завершен успешно!${NC}"
else
    echo -e "${RED}❌ Скрипт завершен с ошибкой (код: $EXIT_CODE)${NC}"
fi
echo "=========================================="

exit $EXIT_CODE
