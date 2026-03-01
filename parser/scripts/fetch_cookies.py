"""
Получение cookies через Undetected Playwright

Включает:
- undetected-playwright как база
- Canvas fingerprint spoofing (критично!)
- WebGL vendor/renderer маскировка
- Динамический fingerprint для каждого запуска
- Улучшенная имитация поведения человека
- Randomization всех параметров
"""

import json
import random
import time

from playwright.sync_api import sync_playwright
from undetected_playwright import stealth_sync

from config.paths import PARSER_COOKIES_DIR

OUTPUT_FILE = PARSER_COOKIES_DIR / "headers.json"


def generate_session_seed():
    """
    Генерирует seed для сессии на основе времени
    Это обеспечит уникальность fingerprint между запусками
    но стабильность внутри одной сессии
    """
    return int(time.time() * 1000) % 100000


def random_delay(min_sec=0.5, max_sec=2.0):
    """Случайная задержка для имитации человека"""
    time.sleep(random.uniform(min_sec, max_sec))


def generate_realistic_fingerprint(seed=None):
    """
    Генерирует реалистичный но уникальный fingerprint
    Каждый запуск будет немного отличаться, но правдоподобно

    Args:
        seed: Seed для воспроизводимости (опционально)
    """
    if seed is not None:
        random.seed(seed)

    # Реалистичные конфигурации (статистика из реальных устройств)
    configs = [
        {"cores": 4, "memory": 4, "width": 1366, "height": 768},
        {"cores": 4, "memory": 8, "width": 1920, "height": 1080},
        {"cores": 6, "memory": 8, "width": 1920, "height": 1080},
        {"cores": 8, "memory": 8, "width": 1920, "height": 1080},
        {"cores": 8, "memory": 16, "width": 2560, "height": 1440},
        {"cores": 12, "memory": 16, "width": 2560, "height": 1440},
        {"cores": 16, "memory": 16, "width": 3840, "height": 2160},
    ]

    config = random.choice(configs)

    # Battery с реалистичными значениями
    battery_level = round(random.uniform(0.15, 0.95), 2)
    is_charging = random.choice([True, False, False])  # 33% charging

    # Network с вариациями
    connection_types = ["4g", "4g", "4g", "wifi"]  # 75% 4g, 25% wifi
    connection_type = random.choice(connection_types)

    if connection_type == "wifi":
        rtt = random.randint(5, 30)
        downlink = round(random.uniform(30.0, 100.0), 1)
    else:
        rtt = random.randint(30, 120)
        downlink = round(random.uniform(5.0, 50.0), 1)

    # WebGL vendors (реальные значения)
    webgl_vendors = [
        {
            "vendor": "Google Inc. (Intel)",
            "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
        },
        {
            "vendor": "Google Inc. (NVIDIA)",
            "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)",
        },
        {
            "vendor": "Google Inc. (Intel)",
            "renderer": "ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)",
        },
        {
            "vendor": "Google Inc. (NVIDIA)",
            "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
        },
        {
            "vendor": "Google Inc. (AMD)",
            "renderer": "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
        },
    ]

    webgl = random.choice(webgl_vendors)

    # Canvas noise seed (уникальный для каждой сессии)
    canvas_seed = random.randint(1, 999999)

    return {
        "hardware_cores": config["cores"],
        "device_memory": config["memory"],
        "screen_width": config["width"],
        "screen_height": config["height"],
        "battery_level": battery_level,
        "is_charging": is_charging,
        "connection_type": connection_type,
        "rtt": rtt,
        "downlink": downlink,
        "webgl_vendor": webgl["vendor"],
        "webgl_renderer": webgl["renderer"],
        "canvas_seed": canvas_seed,
    }


def create_advanced_stealth_script(fingerprint):
    """
    Создает JS скрипт с продвинутой маскировкой
    Включает Canvas, WebGL, и другие fingerprint техники
    """
    return f"""
    (function() {{
        'use strict';

        // ============================================
        // CANVAS FINGERPRINT SPOOFING (КРИТИЧНО!)
        // ============================================
        const canvasSeed = {fingerprint["canvas_seed"]};

        // Функция для добавления шума в canvas
        const addCanvasNoise = (canvas, context) => {{
            const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;

            // Добавляем минимальный шум (незаметный визуально)
            for (let i = 0; i < data.length; i += 4) {{
                // Используем seed для воспроизводимости в рамках сессии
                const noise = ((canvasSeed + i) % 10) - 5;
                data[i] = Math.max(0, Math.min(255, data[i] + noise * 0.1));     // R
                data[i+1] = Math.max(0, Math.min(255, data[i+1] + noise * 0.1)); // G
                data[i+2] = Math.max(0, Math.min(255, data[i+2] + noise * 0.1)); // B
            }}

            context.putImageData(imageData, 0, 0);
        }};

        // Патчим toDataURL
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {{
            const context = this.getContext('2d');
            if (context) {{
                addCanvasNoise(this, context);
            }}
            return originalToDataURL.apply(this, arguments);
        }};

        // Патчим toBlob
        const originalToBlob = HTMLCanvasElement.prototype.toBlob;
        HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {{
            const context = this.getContext('2d');
            if (context) {{
                addCanvasNoise(this, context);
            }}
            return originalToBlob.apply(this, arguments);
        }};

        // Патчим getImageData (для более глубокой защиты)
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function() {{
            const imageData = originalGetImageData.apply(this, arguments);
            const data = imageData.data;

            // Минимальный шум в ImageData
            for (let i = 0; i < data.length; i += 100) {{
                const noise = ((canvasSeed + i) % 5) - 2;
                if (data[i] !== undefined) {{
                    data[i] = Math.max(0, Math.min(255, data[i] + noise * 0.05));
                }}
            }}

            return imageData;
        }};

        // ============================================
        // WEBGL FINGERPRINT SPOOFING
        // ============================================
        const getParameterProxied = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            // UNMASKED_VENDOR_WEBGL
            if (parameter === 37445) {{
                return '{fingerprint["webgl_vendor"]}';
            }}
            // UNMASKED_RENDERER_WEBGL
            if (parameter === 37446) {{
                return '{fingerprint["webgl_renderer"]}';
            }}
            return getParameterProxied.apply(this, arguments);
        }};

        // Для WebGL2
        if (window.WebGL2RenderingContext) {{
            const getParameterProxied2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return '{fingerprint["webgl_vendor"]}';
                }}
                if (parameter === 37446) {{
                    return '{fingerprint["webgl_renderer"]}';
                }}
                return getParameterProxied2.apply(this, arguments);
            }};
        }}

        // ============================================
        // BATTERY API
        // ============================================
        Object.defineProperty(navigator, 'getBattery', {{
            value: () => Promise.resolve({{
                charging: {str(fingerprint["is_charging"]).lower()},
                chargingTime: {"Math.random() * 3600" if fingerprint["is_charging"] else "Infinity"},
                dischargingTime: {"Math.random() * 7200" if not fingerprint["is_charging"] else "Infinity"},
                level: {fingerprint["battery_level"]},
                addEventListener: () => {{}},
                removeEventListener: () => {{}}
            }})
        }});

        // ============================================
        // MEDIA DEVICES (улучшенная версия)
        // ============================================
        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
            const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
            navigator.mediaDevices.enumerateDevices = function() {{
                return originalEnumerateDevices.call(this).then(devices => {{
                    // Добавляем реалистичные устройства
                    const fakeDevices = [
                        {{
                            deviceId: 'default',
                            kind: 'audioinput',
                            label: 'Microphone (Realtek High Definition Audio)',
                            groupId: 'group1'
                        }},
                        {{
                            deviceId: 'communications',
                            kind: 'audioinput',
                            label: 'Communications (Realtek High Definition Audio)',
                            groupId: 'group1'
                        }},
                        {{
                            deviceId: 'default',
                            kind: 'audiooutput',
                            label: 'Speakers (Realtek High Definition Audio)',
                            groupId: 'group1'
                        }},
                        {{
                            deviceId: 'vid001',
                            kind: 'videoinput',
                            label: 'HD WebCam (04f2:b604)',
                            groupId: 'group2'
                        }}
                    ];
                    return devices.concat(fakeDevices);
                }});
            }};
        }}

        // ============================================
        // HARDWARE & DEVICE INFO
        // ============================================

        // Device Memory (НЕ переопределяем если уже есть в undetected-playwright)
        if (!Object.getOwnPropertyDescriptor(navigator, 'deviceMemory')) {{
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {fingerprint["device_memory"]}
            }});
        }}

        // Connection Info
        Object.defineProperty(navigator, 'connection', {{
            get: () => ({{
                effectiveType: '{fingerprint["connection_type"]}',
                rtt: {fingerprint["rtt"]},
                downlink: {fingerprint["downlink"]},
                saveData: false,
                addEventListener: () => {{}},
                removeEventListener: () => {{}}
            }})
        }});

        // ============================================
        // SCREEN & WINDOW
        // ============================================

        // Screen properties (реалистичные значения)
        Object.defineProperty(screen, 'availWidth', {{
            get: () => {fingerprint["screen_width"]}
        }});
        Object.defineProperty(screen, 'availHeight', {{
            get: () => {fingerprint["screen_height"] - 40} // Минус taskbar
        }});
        Object.defineProperty(screen, 'width', {{
            get: () => {fingerprint["screen_width"]}
        }});
        Object.defineProperty(screen, 'height', {{
            get: () => {fingerprint["screen_height"]}
        }});

        // Color Depth (реалистичное значение)
        Object.defineProperty(screen, 'colorDepth', {{
            get: () => 24
        }});
        Object.defineProperty(screen, 'pixelDepth', {{
            get: () => 24
        }});

        // ============================================
        // TIMING ATTACKS PROTECTION
        // ============================================

        // Добавляем небольшой шум в performance.now()
        const originalPerformanceNow = performance.now;
        const timeShift = Math.random() * 10;
        performance.now = function() {{
            return originalPerformanceNow.call(this) + timeShift + (Math.random() - 0.5) * 0.1;
        }};

        // Date.now() с небольшим шумом
        const originalDateNow = Date.now;
        Date.now = function() {{
            return originalDateNow.call(this) + Math.floor(timeShift);
        }};

        // ============================================
        // AUDIO CONTEXT FINGERPRINT SPOOFING
        // ============================================
        const audioContextProto = AudioContext.prototype;
        const originalGetChannelData = AudioBuffer.prototype.getChannelData;

        AudioBuffer.prototype.getChannelData = function(channel) {{
            const channelData = originalGetChannelData.call(this, channel);

            // Добавляем минимальный шум в аудио fingerprint
            for (let i = 0; i < channelData.length; i += 100) {{
                channelData[i] = channelData[i] + (Math.random() - 0.5) * 0.0000001;
            }}

            return channelData;
        }};

        // ============================================
        // CLIENT RECTS SPOOFING
        // ============================================
        const originalGetClientRects = Element.prototype.getClientRects;
        Element.prototype.getClientRects = function() {{
            const rects = originalGetClientRects.apply(this, arguments);

            // Добавляем минимальный шум в размеры (< 0.1px)
            if (rects.length > 0) {{
                const noise = (Math.random() - 0.5) * 0.0001;
                Object.defineProperty(rects[0], 'x', {{
                    get: () => rects[0].x + noise
                }});
                Object.defineProperty(rects[0], 'y', {{
                    get: () => rects[0].y + noise
                }});
            }}

            return rects;
        }};

        console.log('🛡️ Advanced anti-fingerprint protection loaded');

    }})();
    """


def human_mouse_move(page, from_x, from_y, to_x, to_y, steps=None):
    """
    Плавное движение мыши с кривой Безье.
    Имитирует естественное движение руки человека с микро-коррекциями
    """
    if steps is None:
        distance = ((to_x - from_x) ** 2 + (to_y - from_y) ** 2) ** 0.5
        steps = int(distance / 12) + random.randint(15, 25)

    for i in range(steps + 1):
        progress = i / steps

        # Cubic ease-in-out для естественности
        ease = (
            progress * progress * (3 - 2 * progress)
            if progress < 0.5
            else 1 - (1 - progress) * (1 - progress) * (3 - 2 * (1 - progress))
        )

        # Добавляем "дрожание руки" (больше в середине движения)
        wobble_intensity = 1 - abs(progress - 0.5) * 2
        wobble_x = random.uniform(-5, 5) * wobble_intensity
        wobble_y = random.uniform(-5, 5) * wobble_intensity

        current_x = from_x + (to_x - from_x) * ease + wobble_x
        current_y = from_y + (to_y - from_y) * ease + wobble_y

        page.mouse.move(current_x, current_y)

        # Варьируем скорость (иногда замедляемся, иногда ускоряемся)
        if i % 7 == 0:
            delay = random.uniform(0.008, 0.020)
        elif i % 3 == 0:
            delay = random.uniform(0.003, 0.008)
        else:
            delay = random.uniform(0.001, 0.005)

        time.sleep(delay)


def simulate_reading(page, duration_range=(2.0, 5.0)):
    """
    Имитирует чтение контента - небольшие движения глаз/мыши
    """
    duration = random.uniform(*duration_range)
    end_time = time.time() + duration

    viewport = page.viewport_size
    width = viewport["width"]
    height = viewport["height"]

    current_x = random.randint(width // 4, width * 3 // 4)
    current_y = random.randint(height // 4, height // 2)

    moves = 0
    while time.time() < end_time and moves < 8:
        # Небольшие движения как при чтении
        target_x = current_x + random.randint(-150, 150)
        target_y = current_y + random.randint(-80, 80)

        # Ограничиваем координаты
        target_x = max(100, min(width - 100, target_x))
        target_y = max(100, min(height - 100, target_y))

        human_mouse_move(
            page, current_x, current_y, target_x, target_y, steps=random.randint(10, 20)
        )

        current_x, current_y = target_x, target_y
        random_delay(0.5, 1.5)
        moves += 1


def simulate_advanced_human_behavior(page):
    """
    Продвинутая имитация поведения человека
    Включает: осмотр страницы, чтение, прокрутку, hover на элементы
    """
    print("🎭 Имитация действий пользователя (расширенная)...")

    viewport = page.viewport_size
    width = viewport["width"]
    height = viewport["height"]

    # 1. Начальная пауза (человек загружает страницу и смотрит)
    initial_pause = random.uniform(2.5, 5.0)
    print(f"   ⏸️  Начальная пауза: {initial_pause:.1f}с")
    time.sleep(initial_pause)

    # 2. Первые движения мыши (осмотр страницы сверху)
    start_x = random.randint(200, 500)
    start_y = random.randint(150, 300)

    for _ in range(random.randint(2, 4)):
        target_x = random.randint(300, width - 300)
        target_y = random.randint(100, 400)

        human_mouse_move(page, start_x, start_y, target_x, target_y)
        random_delay(0.4, 1.0)

        start_x, start_y = target_x, target_y

    # 3. Прокрутка с "чтением" контента
    scroll_sessions = random.randint(3, 5)
    total_scrolled = 0

    for i in range(scroll_sessions):
        # Прокручиваем
        scroll_amount = random.randint(400, 800)
        if random.random() < 0.2:
            scroll_amount = random.randint(150, 300)

        page.mouse.wheel(0, scroll_amount)
        total_scrolled += scroll_amount

        print(f"   📜 Прокрутка #{i + 1}: {scroll_amount}px")

        # "Читаем" контент после прокрутки
        reading_time = random.uniform(2.0, 4.5)
        simulate_reading(page, (reading_time * 0.5, reading_time))

        # Иногда прокручиваем немного назад
        if i > 0 and random.random() < 0.35:
            back_scroll = random.randint(80, 200)
            page.mouse.wheel(0, -back_scroll)
            print(f"   ⬆️  Прокрутка назад: {back_scroll}px")
            random_delay(0.8, 1.5)

    # 4. Hover на видимые элементы (имитация интереса)
    try:
        safe_selectors = [
            "a:visible",
            'button:visible:not([type="submit"])',
            ".menu-item",
            '[role="button"]',
            "img",
        ]

        for selector in safe_selectors:
            try:
                elements = page.locator(selector).all()
                if elements and len(elements) > 0:
                    # Выбираем 1-2 случайных элемента
                    sample_size = min(random.randint(1, 2), len(elements))
                    selected = random.sample(elements[:10], sample_size)

                    for element in selected:
                        try:
                            if not element.is_visible():
                                continue

                            box = element.bounding_box()
                            if box and box["y"] < height:
                                center_x = box["x"] + box["width"] / 2
                                center_y = box["y"] + box["height"] / 2

                                human_mouse_move(
                                    page, start_x, start_y, center_x, center_y
                                )
                                random_delay(0.5, 1.2)

                                start_x, start_y = center_x, center_y
                                print(f"   👆 Hover на элемент: {selector}")
                                break
                        except:
                            continue
                    break
            except:
                continue
    except Exception as e:
        print(f"   ⚠️  Hover пропущен: {e}")

    # 5. Финальная пауза (человек принимает решение)
    final_pause = random.uniform(1.5, 3.0)
    print(f"   ⏸️  Финальная пауза: {final_pause:.1f}с")
    time.sleep(final_pause)

    print("   ✅ Имитация завершена")


def fetch_cookies(headless: bool = False, fingerprint=None):
    """
    Получает cookies с максимальной защитой от детекции

    Args:
        headless: Запускать браузер без GUI
        fingerprint: Заранее сгенерированный fingerprint (опционально)
    """

    if fingerprint is None:
        fingerprint = generate_realistic_fingerprint()

    print("\n🔐 Fingerprint для сессии:")
    print(f"   CPU cores: {fingerprint['hardware_cores']}")
    print(f"   Memory: {fingerprint['device_memory']} GB")
    print(f"   Screen: {fingerprint['screen_width']}x{fingerprint['screen_height']}")
    print(f"   Connection: {fingerprint['connection_type']}")
    print(f"   WebGL: {fingerprint['webgl_vendor'][:30]}...")
    print(f"   Canvas seed: {fingerprint['canvas_seed']}")

    with sync_playwright() as p:
        print("\n🚀 Запуск undetected browser...")

        # Минимальные browser args (undetected-playwright сам настраивает остальное)
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )

        # Создаем контекст с параметрами из fingerprint
        context = browser.new_context(
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            viewport={
                "width": fingerprint["screen_width"],
                "height": fingerprint["screen_height"],
            },
            screen={
                "width": fingerprint["screen_width"],
                "height": fingerprint["screen_height"],
            },
            permissions=["geolocation"],
            geolocation={"latitude": 37.5665, "longitude": 126.9780},  # Сеул
            device_scale_factor=1.0,
            is_mobile=False,
            has_touch=False,
        )

        # Применяем базовую защиту от undetected-playwright
        print("🛡️  Применение stealth_sync...")
        stealth_sync(context)

        # Применяем продвинутую защиту
        print("🛡️  Применение продвинутой защиты (Canvas, WebGL, Audio)...")
        advanced_script = create_advanced_stealth_script(fingerprint)
        context.add_init_script(advanced_script)

        page = context.new_page()

        print("\n📡 Загрузка Encar.com...")

        try:
            # Переходим на главную
            page.goto(
                "https://www.encar.com/",
                timeout=90000,
                wait_until="domcontentloaded",
            )

            # Ждем полной загрузки (с fallback если networkidle не достигается)
            try:
                page.wait_for_load_state("networkidle", timeout=45000)
                print("✅ Страница полностью загружена (networkidle)")
            except Exception:
                # Если networkidle не достигается - это нормально для сложных сайтов
                print("⚠️  NetworkIdle timeout (это нормально), продолжаем...")
                # Дополнительная пауза для загрузки основного контента
                time.sleep(5)  # Увеличено до 5 секунд

            # Продвинутая имитация поведения
            simulate_advanced_human_behavior(page)

            # Проверяем капчу
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                'iframe[src*="captcha"]',
                ".g-recaptcha",
                "#captcha",
                '[class*="captcha"]',
                '[id*="captcha"]',
            ]

            has_captcha = False
            for selector in captcha_selectors:
                if page.locator(selector).count() > 0:
                    has_captcha = True
                    print(f"\n⚠️  Обнаружена капча! (selector: {selector})")
                    break

            if has_captcha:
                if not headless:
                    print("\n" + "=" * 60)
                    print("⚠️  ТРЕБУЕТСЯ РУЧНОЕ РЕШЕНИЕ КАПЧИ")
                    print("=" * 60)
                    print("Пожалуйста, решите капчу в открытом браузере...")
                    print("Ожидание 90 секунд...")
                    print("=" * 60)
                    time.sleep(90)
                else:
                    print("\n❌ Капча обнаружена в headless режиме")
                    print("\n💡 Рекомендации:")
                    print("1. Запустить с --no-headless")
                    print("2. Использовать residential прокси")
                    browser.close()
                    return False

            # Получаем cookies
            cookies = context.cookies()

            if not cookies:
                print("⚠️  Cookies не были получены!")
                browser.close()
                return False

            print(f"\n✅ Получено {len(cookies)} cookies")

            # Получаем User-Agent и проверяем fingerprint
            ua = page.evaluate("() => navigator.userAgent")

            fingerprint_check = page.evaluate(
                """() => ({
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                webdriver: navigator.webdriver,
                vendor: navigator.vendor,
                productSub: navigator.productSub,
                maxTouchPoints: navigator.maxTouchPoints
            })"""
            )

            print(f"✅ User-Agent: {ua[:60]}...")
            print(f"✅ WebDriver: {fingerprint_check.get('webdriver')}")
            print(f"✅ Platform: {fingerprint_check.get('platform')}")
            print(f"✅ Hardware: {fingerprint_check.get('hardwareConcurrency')} cores")

            # Сохраняем данные
            data_to_save = {
                "cookies": cookies,
                "user_agent": ua,
                "timestamp": time.time(),
                "fingerprint": fingerprint,
                "fingerprint_check": fingerprint_check,
            }

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            print(f"\n✅ Cookies и данные сохранены в {OUTPUT_FILE}")

            browser.close()
            return True

        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback

            traceback.print_exc()
            browser.close()
            return False


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="🚀 Получение cookies с Encar.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  Базовый запуск (headless):
    python fetch_cookies.py

  С GUI (для ручного решения капчи):
    python fetch_cookies.py --no-headless

  Через Xvfb (автоматически определяет):
    ./run_fetch_cookies.sh
        """,
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="ПРИНУДИТЕЛЬНО запустить в headless режиме (не рекомендуется)",
    )
    parser.add_argument(
        "--no-headless", action="store_true", help="Запустить браузер с GUI"
    )

    args = parser.parse_args()

    display_available = os.environ.get("DISPLAY") is not None

    if args.headless and args.no_headless:
        print("❌ Ошибка: нельзя использовать --headless и --no-headless одновременно")
        exit(1)

    if args.headless:
        headless = True
        mode_reason = "принудительно указан --headless"
    elif args.no_headless:
        headless = False
        mode_reason = "указан --no-headless"
    elif display_available:
        headless = False
        mode_reason = f"обнаружен DISPLAY={os.environ.get('DISPLAY')} (Xvfb или X11)"
    else:
        headless = True
        mode_reason = "DISPLAY не обнаружен (нет GUI)"

    print("=" * 60)
    print("     МАКСИМАЛЬНАЯ ЗАЩИТА ОТ ДЕТЕКЦИИ")
    print("=" * 60)
    print(f"Режим: {'🖥️  GUI' if not headless else '👻 Headless'}")
    print(f"Причина: {mode_reason}")
    print("Защита: Canvas, WebGL, Audio, Timing, ClientRects")
    print("=" * 60)

    success = fetch_cookies(headless=headless)

    if success:
        print("\n✅ Программа завершена успешно")
        exit(0)
    else:
        print("\n❌ Программа завершена с ошибкой")
        exit(1)
