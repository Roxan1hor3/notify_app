from typing import Any, Awaitable, Callable

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject

from src.notify.adapters.services.notify_service import NotifyService
from src.notify.adapters.services.telegram_service import TelegramService
from src.notify.telegram_bot.keyboards.base import CancelMenu, PhoneNumberWithCancelMenu
from src.notify.telegram_bot.keyboards.start import StartMenu
from src.notify.telegram_bot.state.repair_connection_state import RepairRequestForm

repair_request_router = Router()


@repair_request_router.message.middleware()
async def chat_command_group_check(
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
) -> Any:
    if event.chat.id < 0:
        return
    return await handler(event, data)


@repair_request_router.message(F.text == "Заявка на ремонт")
async def repair_request_handler(msg: Message, state: FSMContext):
    await state.set_state(RepairRequestForm.fio)
    await msg.answer(text=f"Введіть будь ласка ПІБ.", reply_markup=CancelMenu)


@repair_request_router.message(RepairRequestForm.fio)
async def fio_handler(msg: Message, state: FSMContext):
    await state.update_data({"fio": msg.text})
    await state.set_state(RepairRequestForm.phone_number)
    await msg.answer(
        "Натисніть на кнопку щоб поділитися номером телефону.\n\r"
        "Або введіть самостійно у форматі +380999999999.\n\r",
        reply_markup=PhoneNumberWithCancelMenu,
    )


@repair_request_router.message(F.contact, RepairRequestForm.phone_number)
async def phone_number_contact_handler(msg: Message, state: FSMContext):
    await state.update_data({"phone_number": msg.contact.phone_number})
    await state.set_state(RepairRequestForm.address)
    await msg.answer(
        "Введіть свою адресy.\n\r" "Наприклад: місто Дубровиця вулиця Шкільна 23.\n\r",
        reply_markup=CancelMenu,
    )


@repair_request_router.message(RepairRequestForm.phone_number)
async def phone_number_handler(msg: Message, state: FSMContext):
    await state.update_data({"phone_number": msg.text})
    await state.set_state(RepairRequestForm.address)
    await msg.answer(
        "Введіть свою адресy.\n\r" "Наприклад: місто Дубровиця вулиця Шкільна 23.\n\r",
        reply_markup=CancelMenu,
    )


@repair_request_router.message(RepairRequestForm.address)
async def phone_number_handler(msg: Message, state: FSMContext):
    await state.update_data({"address": msg.text})
    await state.set_state(RepairRequestForm.problem)
    await msg.answer("Опишіть свою проблему.\n\r", reply_markup=CancelMenu)


@repair_request_router.message(RepairRequestForm.problem)
async def address_handler(
    msg: Message,
    state: FSMContext,
    telegram_service: TelegramService,
    notify_service: NotifyService,
):
    await state.update_data({"problem": msg.text})
    data = await state.get_data()
    repair_request = await telegram_service.save_repair_request(
        chat_id=msg.chat.id,
        fio=data["fio"],
        address=data["address"],
        phone_number=data["phone_number"],
        problem=data["problem"],
    )
    await notify_service.send_repair_request_notify(repair_request=repair_request)
    await msg.answer(
        "Ваша заявка відправлена.\n\r"
        f"ПІБ: {repair_request.fio}\n\r"
        f"Адрес: {repair_request.address}\n\r"
        f"Телефон: {repair_request.phone_number}\n\r"
        f"Дата створення: {repair_request.created_at}\n\r"
        f"Проблема: {repair_request.problem}\n\r"
        f"Будь-ласка очікуйте, вам зателефонують.",
        reply_markup=StartMenu,
    )
    await state.clear()
