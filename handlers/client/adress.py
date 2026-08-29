from forms.user import Form
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from handlers.keyboards import get_streets_keyboard, get_door_keyboard

router = Router()


@router.callback_query(Form.address_confirm, F.data == "address_change")
async def process_address_change(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.street)
    await callback.message.edit_text(callback.message.text + "\n\n📝 Указываем новый адрес")
    await callback.message.answer("Выберите улицу:", reply_markup=get_streets_keyboard())
    await callback.answer()

@router.callback_query(Form.address_confirm, F.data == "address_confirm")
async def process_address_confirm(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.door_or_concierge)
    await callback.message.edit_text(callback.message.text + "\n\n✅ Адрес подтверждён")
    await callback.message.answer("Где оставить пакет?", reply_markup=get_door_keyboard())
    await callback.answer()
