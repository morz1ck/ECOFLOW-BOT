from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from handlers.keyboards import get_orders_menu_keyboard, get_orders_list_keyboard, get_order_detail_keyboard
from data_base.models import ADMIN_ID, Order, User
from data_base.db import SessionLocal

router = Router()

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

