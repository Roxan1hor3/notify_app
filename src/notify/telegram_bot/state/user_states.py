from aiogram.fsm.state import State, StatesGroup


class UserForm(StatesGroup):
    phone_number = State()
    personal_account_id = State()
