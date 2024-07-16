from aiogram.dispatcher.filters.state import State, StatesGroup


class UserStates(StatesGroup):
    job_selection = State()
    donate_zsu = State()

    