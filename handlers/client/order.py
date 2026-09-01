from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from forms.user import Form
from handlers.keyboards import (
    get_address_confirm_keyboard, get_streets_keyboard, 
    get_door_keyboard, get_confirm_keyboard)
from data_base.models import User
from data_base.db import SessionLocal
from data_base.crud import has_saved_address, get_price, has_active_subscription

router = Router()


async def proceed_to_address_or_door(message: Message, telegram_id: int, state: FSMContext):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if user and has_saved_address(user):
        await state.update_data(
            street=user.street,
            house_number=user.house_number,
            entrance=user.entrance,
            floor=user.floor,
            room_number=user.room_number,
        )
        await state.set_state(Form.address_confirm)
        await message.answer(
            f"Это ваш адрес?\n\n"
            f"{user.street}, д.{user.house_number}, подъезд {user.entrance}, "
            f"этаж {user.floor}, кв. {user.room_number}",
            reply_markup=get_address_confirm_keyboard(),
        )
    else:
        await state.set_state(Form.street)
        await message.answer("Выберите улицу:", reply_markup=get_streets_keyboard())


@router.callback_query(F.data.in_(["order_now", "order_later"]))
async def process_order_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(order_type=callback.data)

    if callback.data == "order_later":
        await state.set_state(Form.time)
        await callback.message.answer(
            "Укажите время, когда необходимо забрать пакет.\n"
            "Например: 14:00."
        )
        return

    await proceed_to_address_or_door(callback.message, callback.from_user.id, state)
    await callback.answer()


@router.message(Form.time)
async def process_time(message: Message, state: FSMContext):
    await state.update_data(pickup_time=message.text)
    await proceed_to_address_or_door(message, message.from_user.id, state)  


@router.callback_query(Form.street, F.data.startswith("street:"))
async def process_street(callback: CallbackQuery, state: FSMContext):
    street = callback.data.split(":", 1)[1]
    await state.update_data(street=street)
    await state.set_state(Form.address_rest)

    await callback.message.edit_text(f"Улица: {street} ✅")
    await callback.message.answer(
        "Укажите дом, подъезд, этаж и номер квартиры одним сообщением через запятую.\n"
        "Например: «1, 2, 5, 34»"
    )
    await callback.answer()

@router.message(Form.address_rest)
async def process_address_rest(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]

    if len(parts) != 4:
        await message.answer(
            "Не понял формат. Введите через запятую: «дом, подъезд, этаж, квартира», "
            "например «1, 2, 5, 34»"
        )
        return

    house_number, entrance, floor, room_number = parts
    await state.update_data(
        house_number=house_number,
        entrance=entrance,
        floor=floor,
        room_number=room_number,
    )
    await state.set_state(Form.door_or_concierge)
    await message.answer("Где оставить пакет?", reply_markup=get_door_keyboard())

@router.callback_query(Form.door_or_concierge, F.data.in_(["door", "in_person", "concierge"]))
async def process_door_or_concierge(callback: CallbackQuery, state: FSMContext):
    await state.update_data(door_or_concierge=callback.data)

    with SessionLocal() as session:
        price = get_price(session, "single_order")
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        subscribed = has_active_subscription(user)

    data = await state.get_data()
    order_type_text = "сейчас" if data["order_type"] == "order_now" else "на время"
    door_text = {
        "door": "у двери",
        "in_person": "отдать лично",
        "concierge": "у консьержа",
    }.get(data["door_or_concierge"], data["door_or_concierge"])

    text = f"Проверьте заказ:\nТип: {order_type_text}\n"
    if data["order_type"] == "order_later":
        text += f"Время: {data['pickup_time']}\n"
    text += (
        f"Улица: {data['street']}\n"
        f"Дом: №{data['house_number']}, подъезд: {data['entrance']}, "
        f"этаж: {data['floor']}, кв: {data['room_number']}\n"
        f"Куда положить: {door_text}\n\n"
    )

    if subscribed:
        text += "📦 У вас активна подписка — вынос бесплатный"
        await state.set_state(Form.confirm)
        await callback.message.answer(text, reply_markup=get_confirm_keyboard())
    else:
        text += f"Стоимость: {price}₽"
        await state.set_state(Form.confirm)
        await callback.message.answer(text, reply_markup=get_confirm_keyboard())

    await callback.answer()