from aiogram.dispatcher.filters.state import State, StatesGroup


class UserStates(StatesGroup):
    start = State()
    post_view = State()
    about = State()
    filter = State()
    easter_egg = State()
