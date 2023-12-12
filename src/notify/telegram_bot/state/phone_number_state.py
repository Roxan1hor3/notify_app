from aiogram.fsm.state import State, StatesGroup


class PhoneNumberForm(StatesGroup):
    phone_number = State()
