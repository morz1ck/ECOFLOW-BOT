import json
from handlers.keyboards import get_tariffs_keyboard
from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from data_base.db import SessionLocal
from data_base.models import User
from data_base.crud import get_price, has_active_subscription
from handlers.client.payment import YOOKASSA_TOKEN

router = Router()

@router.callback_query(F.data == 'tariffs')
async def process_tariffs(callback: CallbackQuery):
    with SessionLocal() as session:
        once_price = get_price(session, 'single_order')
        sub_price = get_price(session, 'subscription_month')
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        subscribed = has_active_subscription(user)

    text = (
        '💰 <b>Тарифы и подписки сервиса</b>\n\n'
        '<b>Акция в честь старта сервиса!</b>\n'
        'Тарификация фиксированная на все виды услуг (до 30 сентября 2026)\n\n'
        '<b>Базовый тариф</b>\n'
        f'Фиксированная цена за один вынос: <b>{once_price}₽</b>\n\n'
        '📦 Месячная подписка <b>«Пакет в день»</b>\n'
        f'{sub_price}₽ / месяц — вынос по подписке от {sub_price // 31}₽\n\n'
        'Оформи месячную подписку и на ежедневной основе курьер будет забирать Ваш мусор.'
    )

    if subscribed:
        until = user.subscription_until.strftime('%d.%m.%Y')
        text += f'\n\n✅ У вас активна подписка до {until}'

    await callback.message.answer(text, parse_mode='html', reply_markup=get_tariffs_keyboard(subscribed))
    await callback.answer()


@router.callback_query(F.data == "buy_subscription")
async def buy_subscription(callback: CallbackQuery):
    with SessionLocal() as session:
        sub_price = get_price(session, "subscription_month")

    provider_data = json.dumps({
        "receipt": {
            "items": [
                {
                    "description": "Подписка ЭкоПоток на месяц",
                    "quantity": "1.00",
                    "amount": {"value": f"{sub_price:.2f}", "currency": "RUB"},
                    "vat_code": 1
                }
            ]
        }
    })

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Подписка ЭкоПоток на месяц",
        description="Безлимитный вынос мусора на 30 дней — до 1 раза в день",
        payload="subscription_payment",
        provider_token=YOOKASSA_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Подписка на месяц", amount=sub_price * 100)],
        need_phone_number=True,
        send_phone_number_to_provider=True,
        provider_data=provider_data,
    )
    await callback.answer()


@router.callback_query(F.data == 'subscription_status')
async def subscription_status(callback: CallbackQuery):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        subscribed = has_active_subscription(user)

    if subscribed:
        until = user.subscription_until.strftime('%d.%m.%Y')
        await callback.message.answer(f"✅ У вас активна подписка до {until}")
    else:
        with SessionLocal() as session:
            sub_price = get_price(session, "subscription_month")
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📦 Купить подписку", callback_data="buy_subscription")]]
        )
        await callback.message.answer(
            f"У вас пока нет подписки.\n\n📦 Месячная подписка — {sub_price}₽",
            reply_markup=keyboard,
        )

    await callback.answer()