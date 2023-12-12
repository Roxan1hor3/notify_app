from aiogram.fsm.state import State, StatesGroup


class ConnectionRequestForm(StatesGroup):
    fio = State()
    phone_number = State()
    address = State()
