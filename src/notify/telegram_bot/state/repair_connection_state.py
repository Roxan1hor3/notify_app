from aiogram.fsm.state import State, StatesGroup


class RepairRequestForm(StatesGroup):
    fio = State()
    phone_number = State()
    address = State()
    problem = State()
