from aiogram import F, Router
from aiogram.types import Message

from src.notify.telegram_bot.keyboards.start import StartMenu

tariffs_router = Router()


@tariffs_router.message(F.text == "Тарифи")
async def connection_request_handler(msg: Message):
    await msg.answer(
        text='''
    Тарифні плани
''',
    )
    await msg.answer(
        text='''
        "Стандарт"
         Швидкість, Мбіт/с 12 / 12  
         Абонплата, грн./міс 100
    ''',
    )
    await msg.answer(
        text='''
        "Оптимальний" 
        Швидкість, Мбіт/с 20 / 20  
        Абонплата, грн./міс 120
    ''',
    )
    await msg.answer(
        text='''
        "Плюс" 
        Швидкість, Мбіт/с 50 / 50   
        Абонплата, грн./міс 150
    ''',
    )
    await msg.answer(
        text='''
        "Ультра" 
        Швидкість, Мбіт/с до 100 / 100 
        Абонплата, грн./міс 170
    ''',
    reply_markup=StartMenu,
    )
