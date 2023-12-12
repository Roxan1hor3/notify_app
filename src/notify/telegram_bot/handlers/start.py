from typing import Any, Awaitable, Callable

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject

from src.notify.adapters.services.telegram_service import TelegramService
from src.notify.telegram_bot.keyboards.base import PhoneNumberMenu
from src.notify.telegram_bot.keyboards.start import StartMenu
from src.notify.telegram_bot.state.phone_number_state import PhoneNumberForm

start_router = Router()


@start_router.message.middleware()
async def chat_command_group_check(
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
) -> Any:
    if event.chat.id < 0:
        return
    return await handler(event, data)


@start_router.message(CommandStart())
async def start_payment_form(msg: Message, state: FSMContext):
    await state.set_state(PhoneNumberForm.phone_number)
    await msg.answer(
        "Нажміть на кнопку щоб поділитися номером телефона.",
        reply_markup=PhoneNumberMenu,
    )


@start_router.message(F.contact, PhoneNumberForm.phone_number)
async def phone_number_handler(
    msg: Message, state: FSMContext, telegram_service: TelegramService
):
    await state.update_data({"phone_number": msg.contact.phone_number})
    data = await state.get_data()
    await telegram_service.save_new_user(
        chat_id=msg.chat.id,
        first_name=msg.from_user.first_name,
        last_name=msg.from_user.last_name,
        username=msg.from_user.username,
        phone_number=data["phone_number"],
    )
    await state.clear()
    await msg.answer(
        text=f"Збережений номер телефона: {msg.contact.phone_number}.\n\r",
    )
    await msg.answer(
        "Нажміть на кнопку для команди боту.",
        reply_markup=StartMenu,
    )


@start_router.message(F.text == "До стартового меню")
async def to_start_menu_handler(msg: Message):
    await msg.answer(
        "Нажміть на кнопку для команди боту.",
        reply_markup=StartMenu,
    )


@start_router.message()
async def random_message_handler(msg: Message):
    await msg.answer(
        text=f"Натисніть на якусь кнопку.",
        reply_markup=StartMenu,
    )
