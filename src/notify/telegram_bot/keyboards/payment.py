from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

PaymentMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Баланс"),
            KeyboardButton(text="Місячна оплата"),
            KeyboardButton(text="До стартового меню"),
        ]
    ],
    one_time_keyboard=True,
    resize_keyboard=True,
)
