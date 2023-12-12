from aiogram import F, Router
from aiogram.types import Message

from src.notify.telegram_bot.keyboards.start import StartMenu

contact_router = Router()


@contact_router.message(F.text == "Контакти")
async def connection_request_handler(msg: Message):
    await msg.answer(
        text=f"Електронна адреса: nstream@ukr.net\n\r"
        f"Телефони тех.підтримки: 098 031 6000 , 095 500 2221.",
        reply_markup=StartMenu,
    )
