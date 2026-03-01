import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config.settings import bot_settings
from logger.logging import get_bot_logger

from bot.handlers.common import common_router
from bot.handlers.parser import parser_router

logger = get_bot_logger(__name__)

async def main():
    logger.info(f'Запуск бота...')

    bot = Bot(token=bot_settings.token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_routers(
        common_router,
        parser_router,
    )

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Бот остановлен пользователем')
    except Exception as e:
        logger.error(f'Критическая ошибка: {e}', exc_info=True)