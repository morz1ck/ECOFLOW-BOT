from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from forms.user import Form
from handlers.keyboards import (
    get_address_confirm_keyboard, get_streets_keyboard, 
    get_door_keyboard, get_confirm_keyboard, get_trash_type_keyboard)
from data_base.models import User
from data_base.db import SessionLocal
from data_base.crud import has_saved_address, get_price, has_active_subscription, has_active_large_subscription, calculate_order_price

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

async def process_order_type_common(message: Message, user_id: int, order_type: str, state: FSMContext):
    await state.update_data(order_type=order_type)
    await state.set_state(Form.trash_type)

    await message.answer("Выберите тип мусора:", reply_markup=get_trash_type_keyboard())
    

@router.callback_query(F.data.in_(["order_now", "order_later"]))
async def process_order_type(
    callback: CallbackQuery,
    state: FSMContext
):
    await process_order_type_common(
        callback.message,
        callback.from_user.id,
        callback.data,
        state
    )

    await callback.answer()

@router.message(F.text.in_(["🗑 Вынести мусор сейчас", "🕐 Заказать на время"]))
async def process_order_type_reply(message: Message, state: FSMContext):
    order_type = {
        "🗑 Вынести мусор сейчас": "order_now",
        "🕐 Заказать на время": "order_later",
    }[message.text]

    await process_order_type_common(
        message,
        message.from_user.id,
        order_type,
        state
    )

@router.callback_query(Form.trash_type, F.data.in_(["trash_regular", "trash_large"]))
async def process_trash_type( callback: CallbackQuery, state: FSMContext):
    trash_type = ("regular" if callback.data == "trash_regular" else "large")

    await state.update_data(trash_type=trash_type)
    data = await state.get_data()

    if trash_type == "large":
        await state.set_state(Form.weight)

        await callback.message.answer("Укажите вес мусора в кг (например: 12).\n"
            "Максимальный вес для выноса — 30 кг.")

        await callback.answer()
        return

    if data["order_type"] == "order_later":
        await state.set_state(Form.time)

        await callback.message.answer("Укажите время, когда необходимо забрать пакет.\n"
            "Например: 14:00."
        )
    else:
        await proceed_to_address_or_door(
            callback.message,
            callback.from_user.id,
            state
        )

    await callback.answer()

@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    raw = message.text.strip().replace(",", ".")

    try: weight = float(raw)
    except ValueError:
        await message.answer("Введите вес числом, например: 12 или 7.5")
        return

    if weight < 5:
        await message.answer("Минимальный вес крупногабаритного мусора — 5 кг.")
        return

    if weight > 30:
        await message.answer("Максимальный вес для выноса — 30 кг.\n"
            "Для более крупных объёмов обратитесь в поддержку.")
        return

    await state.update_data(weight=weight)

    data = await state.get_data()

    if data["order_type"] == "order_later":
        await state.set_state(Form.time)

        await message.answer("Укажите время, когда необходимо забрать пакет.\n"
            "Например: 14:00."
        )
    else:
        await proceed_to_address_or_door(message, message.from_user.id, state)

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
    await state.set_state(Form.confirm)

    data = await state.get_data()

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        subscribed_regular = has_active_subscription(user)
        subscribed_large = has_active_large_subscription(user)
        price, is_free = calculate_order_price(session, data, subscribed_regular, subscribed_large)

    order_type_text = "сейчас" if data["order_type"] == "order_now" else "на время"
    door_text = {
        "door": "у двери",
        "in_person": "отдать лично",
        "concierge": "у консьержа",
    }.get(data["door_or_concierge"], data["door_or_concierge"])

    trash_type_text = (
        "Обычный мусор" if data.get("trash_type", "regular") == "regular"
        else f"Крупногабаритный, вес: {data['weight']} кг"
    )

    text = f"Проверьте заказ:\nТип: {order_type_text}\nМусор: {trash_type_text}\n"
    if data["order_type"] == "order_later":
        text += f"Время: {data['pickup_time']}\n"
    text += (
        f"Улица: {data['street']}\n"
        f"Дом: №{data['house_number']}, подъезд: {data['entrance']}, "
        f"этаж: {data['floor']}, кв: {data['room_number']}\n"
        f"Куда положить: {door_text}\n\n"
    )
    text += "📦 Бесплатно по подписке" if is_free else f"Стоимость: {price:g}₽"

    await callback.message.answer(text, reply_markup=get_confirm_keyboard())
    await callback.answer()