from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

UserMenu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Баланс"), KeyboardButton(text="Місячна оплата")]],
    one_time_keyboard=True,
    resize_keyboard=True,
)

PhoneNumberButton = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Поділитись номером телефона", request_contact=True)]
    ],
    one_time_keyboard=True,
    resize_keyboard=True,
)
