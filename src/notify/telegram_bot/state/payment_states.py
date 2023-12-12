from aiogram.fsm.state import State, StatesGroup


class PaymentForm(StatesGroup):
    personal_account_id = State()
