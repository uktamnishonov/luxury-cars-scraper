from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputMediaPhoto

from bot.states.parser import ParserState
from bot.utils.validator import validate_url
from logger.logging import get_bot_logger

from parser.collectors.details_fetcher import VehicleDetailsFetcher

logger = get_bot_logger(__name__)
parser_router = Router()


@parser_router.message(ParserState.waiting_for_link, F.text)
async def parser_handler(message: Message, state: FSMContext):
    url = message.text.strip()

    logger.info(f"Пользователь {message.from_user.id} отправил URL {url}")

    if not url.startswith("http"):
        await message.answer(
            text='⚠️ Отправьте корректную ссылку на автомобиль с сайта <a href="https://encar.com">Encar</a>.'
        )
        return

    car_id = validate_url(url)
    if car_id:
        logger.info(
            f"ID от пользователя {message.from_user.id} успешно извлечен {car_id}"
        )

        processing_msg = await message.answer(
            f"🔍 Получаю информацию об автомобиле...\n"
            f"🆔 ID: <code>{car_id}</code>\n"
            f"⏳ Это может занять 10-30 секунд...",
        )

        try:
            fetcher = VehicleDetailsFetcher()
            data = fetcher.fetch_single_car_details(car_id)

            answer_message = "🚗 <b>Информация об автомобиле</b>\n\n"

            # Основная информация
            if data.get("brand"):
                answer_message += f"🏢 Марка: <b>{data['brand']}</b>\n"
            if data.get("model"):
                answer_message += f"🚙 Модель: <b>{data['model']}</b>\n"
            if data.get("year"):
                answer_message += f"📅 Год: <b>{data['year']}</b>\n"
            if data.get("price"):
                answer_message += f"💰 Цена: <b>{data['price']} ₩</b>\n"
            if data.get("mileage"):
                answer_message += f"📏 Пробег: <b>{data['mileage']} км</b>\n"

            answer_message += "\n<b>Характеристики:</b>\n"

            if data.get("fuel"):
                answer_message += f"⛽ Топливо: {data['fuel']}\n"
            if data.get("transmission"):
                answer_message += f"⚙️ КПП: {data['transmission']}\n"
            if data.get("color"):
                answer_message += f"🎨 Цвет: {data['color']}\n"
            if data.get("displacement"):
                answer_message += f"🔧 Объем: {data['displacement']}\n"
            if data.get("seating"):
                answer_message += f"👥 Мест: {data['seating']}\n"

            # Дополнительно
            if data.get("region"):
                answer_message += f"\n📍 Регион: {data['region']}\n"
            if data.get("vehnumber"):
                answer_message += f"🔢 Номер: {data['vehnumber']}\n"

            images = data.get("images", [])[:10]
            if images:
                media_group = []
                for i, url in enumerate(images):
                    if i == 0:
                        media_group.append(
                            InputMediaPhoto(media=url, caption=answer_message)
                        )
                    else:
                        media_group.append(InputMediaPhoto(media=url))

                try:
                    await processing_msg.delete()
                    await message.answer_media_group(media_group)
                except Exception as e:
                    logger.error(f"Ошибка отправки изображений: {e}")

        except Exception as e:
            logger.error(e)

    else:
        logger.info(f"Не удалось извлечь ID от пользователя {message.from_user.id}")

        await message.answer(text="Не удалось извлечь ID")
        await state.clear()
