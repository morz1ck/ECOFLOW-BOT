import json
import os
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from forms.user import Form
from data_base.db import SessionLocal
from data_base.db import get_or_create_user
from data_base.models import Order, User
from datetime import datetime
from dotenv import load_dotenv
from aiogram.types import LabeledPrice, PreCheckoutQuery, LinkPreviewOptions
from data_base.models import Order, User, Price
from data_base.crud import get_price, set_price, get_all_prices, has_saved_address


load_dotenv()
YOOKASSA_TOKEN = os.getenv("YOOKASSA_TEST_LIVE")

router = Router()

ADMIN_ID = [1097519866, 1473358975, 6511035077]

STREETS = ['ул. Голландская', 'ул. Ясная', 'ул. Тюльпанов']

def get_main_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Вынести мусор сейчас", callback_data="order_now")],
            [InlineKeyboardButton(text="🕐 Заказать на время", callback_data="order_later")],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="ℹ️ Как это работает", callback_data="how_it_works")],
            [InlineKeyboardButton(text='💰 Тарифы', callback_data='tariffs')],
        ]
    )


def get_door_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="У двери", callback_data="door")],
            [InlineKeyboardButton(text="Отдам лично", callback_data="in_person")],
            [InlineKeyboardButton(text="У консьержа", callback_data="concierge")],
        ]
    )


def get_confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_order")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")],
        ]
    )

def get_confirm_order_keyboard(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data=f"confirm_out_order:{order_id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"cancel_out_order:{order_id}")],
        ]
    )


def cancel_key():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отменить", callback_data="cancel")],
        ]
    )


def get_orders_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚚 Активные заказы", callback_data="admin_orders:active")],
            [InlineKeyboardButton(text="✅ Завершённые заказы", callback_data="admin_orders:done")],
        ]
    )


def get_orders_list_keyboard(orders, category):
    buttons = []
    for o in orders:
        label = f"№{o.id} — кв.{o.room_number}, {o.status}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"admin_order_detail:{o.id}:{category}")])
    buttons.append([InlineKeyboardButton(text="🔙 В начало списка", callback_data="admin_orders_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_streets_keyboard():
    buttons = [
        [InlineKeyboardButton(text=street, callback_data=f"street:{street}")]
        for street in STREETS
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_order_detail_keyboard(category, order_id=None, status=None):
    buttons = []

    if category == "active" and status == "in_progress":
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Завершить заказ",
                    callback_data=f"complete_order:{order_id}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔙 Назад к списку",
                callback_data=f"admin_orders:{category}",
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🏠 В начало",
                callback_data="admin_orders_menu",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_address_confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="address_confirm")],
            [InlineKeyboardButton(text="📝 Указать другой", callback_data="address_change")],
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋🏾 Привет! Мы — ЭкоПоток! Сервис, который возвращает Вам время!\n\n" \
        "✅ Вынесем за Вас мусор в любое удобное время за пару кликов!\n\n" \
        "🕖 Чтобы воспользоваться услугой прямо сейчас, нажмите на кнопку «Вынести мусор сейчас», и следуйте инструкции.\n\n" \
        "‼️ Если у Вас возникли вопросы или проблемы с сервисом, обратитесь в нашу <a href='t.me/ecoflowsupport'>поддержку</a>.",
        reply_markup=get_main_inline_keyboard(), parse_mode='HTML', disable_web_page_preview=True
    )
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

@router.callback_query(Form.address_confirm, F.data == "address_confirm")
async def process_address_confirm(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.door_or_concierge)
    await callback.message.edit_text(callback.message.text + "\n\n✅ Адрес подтверждён")
    await callback.message.answer("Где оставить пакет?", reply_markup=get_door_keyboard())
    await callback.answer()


@router.callback_query(Form.address_confirm, F.data == "address_change")
async def process_address_change(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.street)
    await callback.message.edit_text(callback.message.text + "\n\n📝 Указываем новый адрес")
    await callback.message.answer("Выберите улицу:", reply_markup=get_streets_keyboard())
    await callback.answer()

@router.message(Form.time)
async def process_time(message: Message, state: FSMContext):
    await state.update_data(pickup_time=message.text)
    await state.set_state(Form.street)
    await message.answer("Выберите улицу:", reply_markup=get_streets_keyboard())

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


@router.callback_query(F.data == "my_orders")
async def process_my_orders(callback: CallbackQuery):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        if user is None:
            await callback.message.answer("У вас пока нет заказов.")
            await callback.answer()
            return

        orders = (
            session.query(Order)
            .filter_by(user_id=user.id)
            .order_by(Order.created_at.desc())
            .limit(5)
            .all()
        )

        if not orders:
            await callback.message.answer("У вас пока нет заказов.")
        else:
            text = "📦 Ваши последние заказы:\n\n"
            for o in orders:
                status_emoji = {"new": "🆕", "in_progress": "🚚", "done": "✅", "cancelled": "❌"}.get(o.status, "")
                text += f"{status_emoji} №{o.id} — {o.created_at.strftime('%d.%m %H:%M')} — {o.status}\n"
            await callback.message.answer(text)

    await callback.answer()

#todo: добавить кнопку оформление подписки: показывать проверку по наличию подписки (нет - показать, да - не показать)
@router.callback_query(F.data == 'tariffs')
async def process_tariffs(callback: CallbackQuery):
    with SessionLocal() as session:
        once_price = get_price(session, 'single_order')
        sub_price = get_price(session, 'subscription_month')

    await callback.message.answer(
        '💰 <b>Тарифы и подписки сервиса</b>\n\n' \
        '<b>Акция в честь старта сервиса!</b>\n' \
        'Тарификация фиксированная на все виды услуг (до 30 сентября 2026)\n\n' \
        '<b>Базовый тариф</b>\n'
        f'Фиксированная цена за один вынос: <b>{once_price}</b>\n\n' \
        '📦 Месячная подписка <b>«Пакет в день»</b>\n' \
        f'{sub_price}₽ / месяц — вынос по подписке от {sub_price // 31}₽\n\n' \
        'Оформи месячную подписку и на ежедневной основе курьер будет забирать Ваш мусор. Достаточно нажать кнопку <b>«Вынести мусор сейчас»</b>',
        parse_mode='html',
    )
    await callback.answer()


@router.callback_query(F.data == "how_it_works")
async def process_how_it_works(callback: CallbackQuery):
    await callback.message.answer(
        "🔑 Элементарная система работы бота подразумевает следующие шаги:\n\n" \
        "1. Нажать на кнопку «Вынести мусор сейчас» / «Заказать на время»\n" \
        "2. Указать адрес.\n" \
        "3. Выбрать способ выдачи мусора курьеру из предложенных.\n" \
        "4. Оплатить разовую выноску / Оформить месячную подписку на вынос мусора.\n" \
        "5. Далее наш курьер прибивает на адрес, забирает Ваш мусор и доставляет его до ближайшего мусорного бака общего пользования.\n\n" \
        "🗑 Мусор уходит сам. Ваше время остается с Вами."
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

    with SessionLocal() as session:
        price = get_price(session, "single_order")

    data = await state.get_data()
    order_type_text = "сейчас" if data["order_type"] == "order_now" else "на время"

    door_text = {
        "door": "у двери",
        "in_person": "отдать лично",
        "concierge": "у консьержа",
    }.get(data["door_or_concierge"], data["door_or_concierge"])

    text = (
        f"Проверьте заказ:\n"
        f"Тип: {order_type_text}\n"
    )
    if data["order_type"] == "order_later":
        text += f"Время: {data['pickup_time']}\n"
    text += (
        f"Улица: {data['street']}\n"
        f"Дом: №{data['house_number']}, подъезд: {data['entrance']}, "
        f"этаж: {data['floor']}, кв: {data['room_number']}\n"
        f"Куда положить: {door_text}\n\n"
        f"Стоимость: {price}₽"
    )

    await callback.message.answer(text, reply_markup=get_confirm_keyboard())
    await callback.answer()


@router.callback_query(Form.confirm, F.data == "confirm_order")
async def process_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    with SessionLocal() as session:
        price = get_price(session, "single_order")


    door_text = {
        "door": "у двери",
        "in_person": "отдать лично",
        "concierge": "у консьержа",
    }.get(data["door_or_concierge"], data["door_or_concierge"])

    order_type_text = "сейчас" if data["order_type"] == "order_now" else "на время"

    description = f"{order_type_text}, {door_text}"
    if data["order_type"] == "order_later":
        description += f", время: {data['pickup_time']}"

    await callback.message.edit_reply_markup(reply_markup=None)

    provider_data = json.dumps({
        "receipt": {
            "items": [
                {
                    "description": "Вынос мусора",
                    "quantity": "1.00",
                    "amount": {
                        "value": f"{price:.2f}",
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }
            ]
        }
    })

    """ print("DEBUG SEND_INVOICE:", {
        "chat_id": callback.from_user.id, 
        "title": "Вынос мусора 🗑",
        "description": description,
        "payload": "order_payment",
        "provider_token": YOOKASSA_TOKEN,
        "currency": "RUB",
        "prices": [{"label": "Вынос мусора", "amount": 150 * 100}],
        "need_phone_number": True,
        "send_phone_number_to_provider": True,
        "provider_data": provider_data,
    })"""
    
    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Вынос мусора 🗑",
        description=description,
        payload="order_payment",
        provider_token=YOOKASSA_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Вынос мусора", amount=price * 100)],
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
    data = await state.get_data()
    print("DEBUG STATE DATA:", data)   # ← добавили

    order_type_text = "сейчас" if data["order_type"] == "order_now" else "на время"

    with SessionLocal() as session:
        price = get_price(session, "single_order")
        user = get_or_create_user(session,
            telegram_id=message.from_user.id,
            username=message.from_user.username)

        print("DEBUG USER BEFORE:", user.telegram_id, user.street)  # ← добавили

        user.street = data["street"]
        user.house_number = data["house_number"]
        user.entrance = data["entrance"]
        user.floor = data["floor"]
        user.room_number = data["room_number"]

        print("DEBUG USER AFTER ASSIGN:", user.telegram_id, user.street)  # ← добавили

        door_text = {
            "door": "у двери",
            "in_person": "отдать лично",
            "concierge": "у консьержа",
        }.get(data["door_or_concierge"], data["door_or_concierge"])

        order = Order(
            user_id=user.id,
            order_type=data["order_type"],
            pickup_time=data.get("pickup_time"),
            street=data["street"],
            house_number=data["house_number"],
            entrance=data["entrance"],
            floor=data["floor"],
            room_number=data["room_number"],
            door_or_concierge=data["door_or_concierge"],
            status="new",
            price=price,
            is_paid=True,
        )
        session.add(order)
        session.commit()
        order_id = order.id

        print("DEBUG USER AFTER COMMIT:", user.telegram_id, user.street)  # ← добавили

    admin_text = (
        f"📥 Новый заказ №{order_id} (оплачен ✅)\n"
        f"Клиент: @{message.from_user.username or message.from_user.id}\n"
        f"Тип: {order_type_text}\n"
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
        sent_message = await message.bot.send_message(
            admin_id, admin_text, reply_markup=get_confirm_order_keyboard(order_id)
        )
        admin_messages[str(admin_id)] = sent_message.message_id

    with SessionLocal() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        order.admin_messages = json.dumps(admin_messages)
        session.commit()

    await message.answer("Оплата прошла успешно ✅ Заказ отправлен курьеру, ожидайте подтверждения ⏳")
    await state.clear()


@router.callback_query(Form.confirm, F.data == "cancel_order")
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Заказ отменён.")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_out_order:"))
async def process_accept_order(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])

    with SessionLocal() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if order is None:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        order.status = "in_progress"
        session.commit()

        client = session.query(User).filter_by(id=order.user_id).first()
        client_telegram_id = client.telegram_id

    await callback.bot.send_message(
        client_telegram_id,
        "Курьер принял ваш заказ, скоро будет у вас 🚀",
    )
    await callback.message.edit_text(callback.message.text + "\n\n✅ Принято в работу")
    await callback.answer("Заказ принят")


@router.callback_query(F.data.startswith("cancel_out_order:"))
async def process_reject_order(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])

    with SessionLocal() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if order is None:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        order.status = "cancelled"
        session.commit()

        client = session.query(User).filter_by(id=order.user_id).first()
        client_telegram_id = client.telegram_id

    await callback.bot.send_message(
        client_telegram_id,
        "К сожалению, курьер не смог принять ваш заказ. Попробуйте оформить его позже.",
    )
    await callback.message.edit_text(callback.message.text + "\n\n❌ Отклонено")
    await callback.answer("Заказ отклонён")

@router.message(Command("orders"))
async def admin_orders_command(message: Message):
    if message.from_user.id not in ADMIN_ID:
        return
    await message.answer("📋 Список заказов", reply_markup=get_orders_menu_keyboard())


@router.callback_query(F.data == "admin_orders_menu")
async def admin_orders_menu(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    await callback.message.edit_text("📋 Список заказов", reply_markup=get_orders_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_orders:"))
async def admin_orders_list(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    category = callback.data.split(":")[1]
    statuses = ["new", "in_progress"] if category == "active" else ["done", "cancelled"]

    with SessionLocal() as session:
        orders = (
            session.query(Order)
            .filter(Order.status.in_(statuses))
            .order_by(Order.created_at.desc())
            .limit(20)
            .all()
        )

        if not orders:
            title = "🚚 Активные заказы" if category == "active" else "✅ Завершённые заказы"
            await callback.message.edit_text(
                f"{title}\n\nЗдесь пока пусто.",
                reply_markup=get_orders_list_keyboard([], category),
            )
            await callback.answer()
            return

        title = "🚚 Активные заказы" if category == "active" else "✅ Завершённые заказы"
        await callback.message.edit_text(title, reply_markup=get_orders_list_keyboard(orders, category))

    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_detail:"))
async def admin_order_detail(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    _, order_id_str, category = callback.data.split(":")
    order_id = int(order_id_str)

    with SessionLocal() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if order is None:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        client = session.query(User).filter_by(id=order.user_id).first()

        order_type_text = "сейчас" if order.order_type == "order_now" else "на время"
        status_text = {
            "new": "🆕 Новый",
            "in_progress": "🚚 В работе",
            "done": "✅ Выполнен",
            "cancelled": "❌ Отменён",
        }.get(order.status, order.status)

        text = (
            f"📦 Заказ №{order.id}\n\n"
            f"Статус: {status_text}\n"
            f"Клиент: @{client.username or client.telegram_id}\n"
            f"Тип: {order_type_text}\n"
        )
        if order.pickup_time:
            text += f"Время: {order.pickup_time}\n"
        text += (
            f"Дом: №{order.house_number}, подъезд: {order.entrance}, "
            f"этаж: {order.floor}, кв: {order.room_number}\n"
            f"Куда положить: {order.door_or_concierge}\n"
            f"Цена: {order.price}₽\n"
            f"Создан: {order.created_at.strftime('%d.%m %H:%M')}\n"
        )
        if order.completed_at:
            text += f"Завершён: {order.completed_at.strftime('%d.%m %H:%M')}\n"

    await callback.message.edit_text(
    text,
    reply_markup=get_order_detail_keyboard(
        category=category,
        order_id=order.id,
        status=order.status,
    ),
)
    await callback.answer()

@router.callback_query(F.data.startswith("complete_order:"))
async def complete_order(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])

    with SessionLocal() as session:
        order = session.query(Order).filter_by(id=order_id).first()

        if order is None:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        if order.status != "in_progress":
            await callback.answer("Этот заказ нельзя завершить", show_alert=True)
            return

        order.status = "done"
        order.completed_at = datetime.utcnow()

        session.commit()

        client = (
            session.query(User)
            .filter_by(id=order.user_id)
            .first()
        )

        client_telegram_id = client.telegram_id

    await callback.bot.send_message(client_telegram_id,
        "✅ Ваш заказ выполнен. Спасибо, что пользуетесь ЭкоПотоком!",
    )

    with SessionLocal() as session:
        orders = (
            session.query(Order)
            .filter(Order.status.in_(["new", "in_progress"]))
            .order_by(Order.created_at.desc())
            .limit(20)
            .all()
        )

    if orders:
        await callback.message.edit_text("🚚 Активные заказы",
            reply_markup=get_orders_list_keyboard(orders, "active")
        )
    else:
        await callback.message.edit_text("🚚 Активные заказы\n\nЗдесь пока пусто.",
            reply_markup=get_orders_list_keyboard([],"active")
        )

    await callback.answer("Заказ завершён ✅")


def get_change_prices_keyboard(prices):
    buttons = []
    for p in prices:
        buttons.append([InlineKeyboardButton(text=f"{p.label}: {p.value}₽", callback_data=f"changeprice:{p.key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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