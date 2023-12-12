from typing import Any, Awaitable, Callable

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject

from src.notify.adapters.models.message import Message
from src.notify.adapters.services.telegram_service import TelegramService
from src.notify.api.v1.views.users_views import NotifyService
from src.notify.telegram_bot.keyboards.base import CancelMenu, PhoneNumberWithCancelMenu
from src.notify.telegram_bot.keyboards.start import StartMenu
from src.notify.telegram_bot.state.connection_request_state import ConnectionRequestForm

connection_request_router = Router()


@connection_request_router.message.middleware()
async def chat_command_group_check(
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
) -> Any:
    if event.chat.id < 0:
        return
    return await handler(event, data)


@connection_request_router.message(F.text == "Заявка на підключення")
async def connection_request_handler(msg: Message, state: FSMContext):
    await state.set_state(ConnectionRequestForm.fio)
    await msg.answer(text=f"Введіть будь ласка ФІО.", reply_markup=CancelMenu)


@connection_request_router.message(ConnectionRequestForm.fio)
async def fio_handler(msg: Message, state: FSMContext):
    await state.update_data({"fio": msg.text})
    await state.set_state(ConnectionRequestForm.phone_number)
    await msg.answer(
        "Нажміть на кнопку щоб поділитися номером телефона.\n\r"
        "Або введіть самостійно у форматі +380999999999.\n\r",
        reply_markup=PhoneNumberWithCancelMenu,
    )


@connection_request_router.message(F.contact, ConnectionRequestForm.phone_number)
async def phone_number_contact_handler(msg: Message, state: FSMContext):
    await state.update_data({"phone_number": msg.contact.phone_number})
    await state.set_state(ConnectionRequestForm.address)
    await msg.answer(
        "Введіть свій адрес.\n\r" "Наприклад: місто Дубровиця вулиця Шкільна 23.\n\r",
        reply_markup=CancelMenu,
    )


@connection_request_router.message(ConnectionRequestForm.phone_number)
async def phone_number_handler(msg: Message, state: FSMContext):
    await state.update_data({"phone_number": msg.text})
    await state.set_state(ConnectionRequestForm.address)
    await msg.answer(
        "Введіть свій адрес.\n\r" "Наприклад: місто Дубровиця вулиця Шкільна 23.\n\r",
        reply_markup=CancelMenu,
    )


@connection_request_router.message(ConnectionRequestForm.address)
async def address_handler(
    msg: Message,
    state: FSMContext,
    telegram_service: TelegramService,
    notify_service: NotifyService,
):
    await state.update_data({"address": msg.text})
    data = await state.get_data()
    connection_request = await telegram_service.save_connection_request(
        chat_id=msg.chat.id,
        fio=data["fio"],
        address=data["address"],
        phone_number=data["phone_number"],
    )
    await notify_service.send_connection_request_notify(
        connection_request=connection_request
    )
    await msg.answer(
        "Ваша заявка відправлена.\n\r"
        f"ФІО: {connection_request.fio}\n\r"
        f"Адрес: {connection_request.address}\n\r"
        f"Телефон: {connection_request.phone_number}\n\r"
        f"Дата створення: {connection_request.created_at}\n\r"
        f"Будь-ласка очікуйте, вам зателефонують.",
        reply_markup=StartMenu,
    )
    await state.clear()
