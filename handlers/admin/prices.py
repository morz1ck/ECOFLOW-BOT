from handlers.keyboards import get_change_prices_keyboard
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from data_base.models import ADMIN_ID, Price
from data_base.db import SessionLocal
from data_base.crud import get_all_prices, set_price
from forms.user import Form

router = Router()

@router.message(Command("changeprices"))
async def change_prices_command(message: Message):
    if message.from_user.id not in ADMIN_ID:
        return

    with SessionLocal() as session:
        prices = get_all_prices(session)

    await message.answer("Выберите позицию для изменения цены:", reply_markup=get_change_prices_keyboard(prices))


@router.callback_query(F.data.startswith("changeprice:"))
async def change_price_select(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    key = callback.data.split(":")[1]

    with SessionLocal() as session:
        price = session.query(Price).filter_by(key=key).first()

    await state.update_data(price_key=key)
    await state.set_state(Form.new_price)
    await callback.message.answer(f"Введите новую цену для «{price.label}» (текущая: {price.value}₽):")
    await callback.answer()


@router.message(Form.new_price)
async def change_price_apply(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data["price_key"]

    try:
        new_value = int(message.text)
    except ValueError:
        await message.answer("Введите целое число, например 150")
        return

    with SessionLocal() as session:
        set_price(session, key, new_value)
        price = session.query(Price).filter_by(key=key).first()

    await message.answer(f"✅ Цена «{price.label}» обновлена: {new_value}₽")
    await state.clear()