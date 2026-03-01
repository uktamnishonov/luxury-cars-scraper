from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state, default_state
from aiogram.types import Message

from bot.states.parser import ParserState

from logger.logging import get_bot_logger

logger = get_bot_logger(__name__)
common_router = Router()


@common_router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} отправил боту команду /start")

    await state.set_state(ParserState.waiting_for_link)

    await message.answer(
        "👋 Привет! Я бот для парсинга автомобилей с Encar.\n\n"
        "Отправьте мне ссылку на автомобиль, и я получу всю информацию о нём.\n\n"
        "Пример ссылки:\n"
        "<code>https://fem.encar.com/cars/detail/40647630?carid=40647630</code>\n\n"
        "Используйте /help для получения помощи."
    )


@common_router.message(Command("help"), any_state)
async def help_command(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} отправил боту команду /help")

    await message.answer(
        text="ℹ️ <b>Как использовать бота:</b>\n\n"
        "1️⃣ Отправьте ссылку на автомобиль с сайта Encar\n"
        "2️⃣ Бот извлечет ID автомобиля\n"
        "3️⃣ Запустит парсер и получит данные\n"
        "4️⃣ Отправит вам отформатированную информацию\n\n"
        "<b>Команды:</b>\n"
        "/start - Начать работу\n"
        "/help - Помощь\n"
        "/cancel - Отменить текущую операцию"
    )

    await state.set_state(ParserState.waiting_for_link)


@common_router.message(default_state)
async def any_message(message: Message):
    logger.info(f"Пользователь {message.from_user.id} отправил боту неизвестные данные")

    await message.delete()
    await message.answer(
        text="Отправьте мне ссылку на автомобиль, и я получу всю информацию о нём."
    )
