from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

StartMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Заявка на підключення"),
            KeyboardButton(text="Заявка на ремонт"),
            KeyboardButton(text="Стан особового рахунку"),
        ],
        [
            KeyboardButton(text="Контакти"),
            KeyboardButton(text="Тарифи"),
        ],
    ],
    one_time_keyboard=True,
    resize_keyboard=True,
)
