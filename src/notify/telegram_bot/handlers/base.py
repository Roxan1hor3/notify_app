from aiogram import F, Router
from aiogram.fsm.context import FSMContext

from src.notify.adapters.models.message import Message
from src.notify.telegram_bot.keyboards.start import StartMenu

base_router = Router()


@base_router.message(F.text == "Відмінити")
async def cancele_handler(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        text=f"Натисніть на якусь кнопку.",
        reply_markup=StartMenu,
    )
