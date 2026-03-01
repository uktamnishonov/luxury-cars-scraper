from aiogram.fsm.state import StatesGroup, State

class ParserState(StatesGroup):
    waiting_for_link = State()