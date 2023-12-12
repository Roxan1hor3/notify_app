from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

PhoneNumberWithCancelMenu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Поділитись номером телефона", request_contact=True)],
        [KeyboardButton(text="Відмінити")],
    ],
    one_time_keyboard=True,
    resize_keyboard=True,
)
PhoneNumberMenu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Поділитись номером телефона", request_contact=True)],
    ],
    one_time_keyboard=True,
    resize_keyboard=True,
)
CancelMenu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Відмінити")]],
    one_time_keyboard=True,
    resize_keyboard=True,
)
