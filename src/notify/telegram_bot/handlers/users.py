from typing import Any, Awaitable, Callable

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, TelegramObject

from src.notify.adapters.services.telegram_service import TelegramService
from src.notify.telegram_bot.dependency.services import service_manager
from src.notify.telegram_bot.keyboards.users import PhoneNumberButton, UserMenu
from src.notify.telegram_bot.state.user_states import UserForm

router = Router()


@router.message.outer_middleware()
async def database_transaction_middleware(
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
) -> Any:
    data["notify_service"] = await service_manager.notify_service
    data["user_service"] = await service_manager.user_service
    data["telegram_service"] = await service_manager.telegram_service
    return await handler(event, data)


@router.message(CommandStart())
async def start_handler(msg: Message, state: FSMContext):
    await state.set_state(UserForm.phone_number)
    await msg.answer(
        "Нажміть на кнопку щоб поділитися номером телефона.",
        reply_markup=PhoneNumberButton,
    )


@router.message(F.contact, UserForm.phone_number)
async def phone_number_handler(msg: Message, state: FSMContext):
    await state.set_data({"phone_number": msg.contact.phone_number})
    await state.set_state(UserForm.personal_account_id)
    await msg.answer(
        text=f"Збережений номер телефона: {msg.contact.phone_number}.\n\r"
        f"Веддіть будь ласка номер особового рахунку.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(UserForm.personal_account_id)
async def personal_account_id_handler(
    msg: Message, telegram_service: TelegramService, state: FSMContext
):
    if not await telegram_service.retrieve_by_personal_account_id(
        personal_account_id=int(msg.text[:-1])
    ):
        await msg.answer(
            text=f"Такого особового рахунку не знайденно.\n\r" f"Спробуйте ще раз"
        )
        return
    data = await state.get_data()
    await telegram_service.save_new_user(
        chat_id=msg.chat.id,
        first_name=msg.from_user.first_name,
        last_name=msg.from_user.last_name,
        username=msg.from_user.username,
        phone_number=data["phone_number"],
        personal_account_id=msg.text,
    )
    await state.clear()
    await msg.answer(
        text=f"Дякую!!!\n\r"
        f"Ваш номер телефона {data['phone_number']}.\n\r"
        f"Ваш номер особового рахунку {msg.text}.\n\r",
        reply_markup=UserMenu,
    )


@router.message(F.text == "Баланс")
async def start_handler(msg: Message, telegram_service: TelegramService):
    user = await telegram_service.get_user(chat_id=msg.chat.id)
    billing_user = await telegram_service.retrieve_by_personal_account_id(
        personal_account_id=int(user.personal_account_id[:-1])
    )
    await msg.answer(
        text=f"Ваш баланс {billing_user.balance} ГРН.",
        reply_markup=UserMenu,
    )


@router.message(F.text == "Місячна оплата")
async def start_handler(msg: Message, telegram_service: TelegramService):
    user = await telegram_service.get_user(chat_id=msg.chat.id)
    billing_user = await telegram_service.retrieve_by_personal_account_id(
        personal_account_id=int(user.personal_account_id[:-1])
    )
    await msg.answer(
        text=f"Ваша що місячна оплата {billing_user.fee} ГРН.",
        reply_markup=UserMenu,
    )



@router.message()
async def start_handler(msg: Message, telegram_service: TelegramService):
    await msg.answer(
        text=f"Натисніть на якусь кнопку.",
        reply_markup=UserMenu,
    )