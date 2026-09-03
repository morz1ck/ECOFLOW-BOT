import json
import os
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from handlers.keyboards import get_confirm_order_keyboard
from data_base.db import SessionLocal, get_or_create_user
from data_base.models import Order, ADMIN_ID, User
from data_base.crud import has_active_subscription, get_price, has_active_large_subscription, calculate_order_price
from datetime import datetime, timedelta
from dotenv import load_dotenv
from forms.user import Form

router = Router()

load_dotenv()
YOOKASSA_TOKEN = os.getenv("YOOKASSA_TEST_LIVE")


async def finalize_order(bot, telegram_id: int, username: str, data: dict, is_paid: bool, price):
    with SessionLocal() as session:
        user = get_or_create_user(session, telegram_id=telegram_id, username=username)
        user.street = data["street"]
        user.house_number = data["house_number"]
        user.entrance = data["entrance"]
        user.floor = data["floor"]
        user.room_number = data["room_number"]

        order = Order(
            user_id=user.id,
            order_type=data["order_type"],
            pickup_time=data.get("pickup_time"),
            trash_type=data.get("trash_type", "regular"),   # ← новое
            weight=data.get("weight"),                        # ← новое
            street=data["street"],
            house_number=data["house_number"],
            entrance=data["entrance"],
            floor=data["floor"],
            room_number=data["room_number"],
            door_or_concierge=data["door_or_concierge"],
            status="new",
            price=price,
            is_paid=is_paid,
        )
        session.add(order)
        session.commit()
        order_id = order.id

    order_type_text = "сейчас" if data["order_type"] == "order_now" else "на время"
    door_text = {
        "door": "у двери", "in_person": "отдать лично", "concierge": "у консьержа",
    }.get(data["door_or_concierge"], data["door_or_concierge"])

    trash_info = (
        "Обычный мусор" if data.get("trash_type", "regular") == "regular"
        else f"⚠️ Крупногабарит, вес: {data['weight']} кг"
    )

    paid_label = "оплачен ✅" if is_paid else "по подписке 📦"
    admin_text = (
        f"📥 Новый заказ №{order_id} ({paid_label})\n"
        f"Клиент: @{username or telegram_id}\n"
        f"Тип: {order_type_text}\n"
        f"Мусор: {trash_info}\n"
    )
    if data["order_type"] == "order_later":
        admin_text += f"Время: {data['pickup_time']}\n"
    admin_text += (
        f"Дом: № {data['house_number']}, подъезд: {data['entrance']}, "
        f"этаж: {data['floor']}, кв: {data['room_number']}\n"
        f"Куда положить: {door_text}"
    )

    admin_messages = {}
    for admin_id in ADMIN_ID:
        sent_message = await bot.send_message(admin_id, admin_text, reply_markup=get_confirm_order_keyboard(order_id))
        admin_messages[str(admin_id)] = sent_message.message_id

    with SessionLocal() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        order.admin_messages = json.dumps(admin_messages)
        session.commit()

    return order_id

@router.callback_query(Form.confirm, F.data == "confirm_order")
async def process_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        subscribed_regular = has_active_subscription(user)
        subscribed_large = has_active_large_subscription(user)
        price, is_free = calculate_order_price(session, data, subscribed_regular, subscribed_large)

    await callback.message.edit_reply_markup(reply_markup=None)

    if is_free:
        await finalize_order(
            bot=callback.bot,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            data=data,
            is_paid=False,
            price=0,
        )
        await callback.message.answer("Заказ создан по подписке ✅ Ожидайте подтверждения курьера ⏳")
        await state.clear()
        await callback.answer()
        return

    await state.update_data(calculated_price=price)  # фиксируем цену на момент подтверждения

    trash_type = data.get("trash_type", "regular")
    door_text = {
        "door": "у двери",
        "in_person": "отдать лично",
        "concierge": "у консьержа",
    }.get(data["door_or_concierge"], data["door_or_concierge"])
    order_type_text = "сейчас" if data["order_type"] == "order_now" else "на время"

    description = f"{order_type_text}, {door_text}"
    if trash_type == "large":
        description += f", крупногабарит {data['weight']}кг"
    if data["order_type"] == "order_later":
        description += f", время: {data['pickup_time']}"

    provider_data = json.dumps({
        "receipt": {
            "items": [{
                "description": "Вынос мусора" if trash_type == "regular" else "Вынос крупногабаритного мусора",
                "quantity": "1.00",
                "amount": {"value": f"{price:.2f}", "currency": "RUB"},
                "vat_code": 1,
            }]
        }
    })

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Вынос мусора 🗑" if trash_type == "regular" else "Вынос крупногабаритного мусора 📦",
        description=description,
        payload="order_payment",
        provider_token=YOOKASSA_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Вынос мусора", amount=round(price * 100))],
        need_phone_number=True,
        send_phone_number_to_provider=True,
        provider_data=provider_data,
    )
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext):
    payload = message.successful_payment.invoice_payload
    data = await state.get_data()

    if payload == "subscription_payment":
        with SessionLocal() as session:
            user = get_or_create_user(session, telegram_id=message.from_user.id, username=message.from_user.username)
            user.is_subscribed = True
            user.subscription_until = datetime.utcnow() + timedelta(days=30)
            session.commit()
        await message.answer("✅ Подписка «Пакет в день» оформлена на 30 дней!")
        return

    if payload == "large_subscription_payment":
        with SessionLocal() as session:
            user = get_or_create_user(session, telegram_id=message.from_user.id, username=message.from_user.username)
            user.is_subscribed_large = True
            user.subscription_until_large = datetime.utcnow() + timedelta(days=30)
            session.commit()
        await message.answer("✅ Подписка «Крупногабарит» оформлена на 30 дней!")
        return

    price = data.get("calculated_price")
    if price is None:
        with SessionLocal() as session:
            price = get_price(session, "single_order")

    await finalize_order(
        bot=message.bot,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        data=data,
        is_paid=True,
        price=price,
    )
    await message.answer("Оплата прошла успешно ✅ Заказ отправлен курьеру, ожидайте подтверждения ⏳")
    await state.clear()

@router.callback_query(Form.confirm, F.data == "cancel_order")
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Заказ отменён.")
    await state.clear()
    await callback.answer()