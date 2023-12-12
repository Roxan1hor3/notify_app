from typing import Any, Awaitable, Callable

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject

from src.notify.adapters.services.telegram_service import TelegramService
from src.notify.telegram_bot.keyboards.base import CancelMenu
from src.notify.telegram_bot.keyboards.payment import PaymentMenu
from src.notify.telegram_bot.state.payment_states import PaymentForm

payment_router = Router()


@payment_router.message.middleware()
async def chat_command_group_check(
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
) -> Any:
    if event.chat.id < 0:
        return
    return await handler(event, data)


@payment_router.message(F.text == "Стан особового рахунку")
async def start_handler(msg: Message, state: FSMContext):
    await state.set_state(PaymentForm.personal_account_id)
    await msg.answer(
        text=f"Введіть будь ласка номер особового рахунку.", reply_markup=CancelMenu
    )


@payment_router.message(PaymentForm.personal_account_id)
async def personal_account_id_handler(
    msg: Message, telegram_service: TelegramService, state: FSMContext
):
    if not msg.text.isdigit():
        await msg.answer(text=f"Введіть будь-ласка номер.\n\r" f"Наприклад 99999.")
        return
    if not await telegram_service.retrieve_by_user_billing_id(
        billing_id=int(msg.text[:-1])
    ):
        await msg.answer(
            text=f"Такого особового рахунку не знайденно.\n\r" f"Спробуйте ще раз."
        )
        return
    billing_id = int(msg.text[:-1])
    await telegram_service.update_user_billing_and_personal_account_id(
        personal_account_id=int(msg.text),
        billing_id=billing_id,
        chat_id=msg.chat.id,
    )
    await state.clear()
    await msg.answer(
        text=f"Дякую!!!\n\r" f"Ваш номер особового рахунку {msg.text}.\n\r",
        reply_markup=PaymentMenu,
    )


@payment_router.message(F.text == "Баланс")
async def start_handler(msg: Message, telegram_service: TelegramService):
    user = await telegram_service.get_user(chat_id=msg.chat.id)
    billing_user = await telegram_service.retrieve_by_user_billing_id(
        billing_id=user.billing_id
    )
    await msg.answer(
        text=f"Ваш баланс {billing_user.balance} ГРН.",
        reply_markup=PaymentMenu,
    )


@payment_router.message(F.text == "Місячна оплата")
async def start_handler(msg: Message, telegram_service: TelegramService):
    user = await telegram_service.get_user(chat_id=msg.chat.id)
    billing_user = await telegram_service.retrieve_by_user_billing_id(
        billing_id=user.billing_id
    )
    await msg.answer(
        text=f"Ваша щомісячна оплата {billing_user.fee} ГРН.",
        reply_markup=PaymentMenu,
    )
