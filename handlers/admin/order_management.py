from aiogram import F, Router
from aiogram.types import CallbackQuery
from handlers.keyboards import get_orders_list_keyboard, get_back_button
from data_base.models import ADMIN_ID, Order, User
from data_base.db import SessionLocal
from datetime import datetime

router = Router()

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
        "✅ Ваш заказ выполнен. Спасибо, что пользуетесь ЭкоПотоком!", reply_markup=get_back_button()
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
