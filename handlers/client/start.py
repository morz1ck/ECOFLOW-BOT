from handlers import main_router as router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import F
from data_base.db import SessionLocal
from data_base.models import Order, User
from handlers.keyboards import get_main_inline_keyboard



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