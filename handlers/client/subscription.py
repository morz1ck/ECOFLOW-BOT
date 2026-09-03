import json
from handlers.keyboards import get_tariffs_keyboard
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from data_base.db import SessionLocal
from data_base.models import User
from data_base.crud import get_price, has_active_subscription, has_active_large_subscription
from datetime import datetime
from handlers.client.payment import YOOKASSA_TOKEN

router = Router()


@router.message(F.text == '💰 Тарифы')
async def process_tariffs_reply(message: Message):
    with SessionLocal() as session:
        once_price = get_price(session, 'single_order')
        sub_price = get_price(session, 'subscription_month')
        large_price = get_price(session, 'large_subscription')
        large_order_per_kg = get_price(session, 'large_order_per_kg')
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        subscribed_regular = has_active_subscription(user)
        subscribed_large = has_active_large_subscription(user)

    text = (
        '💰 <b>Тарифы и подписки сервиса</b>\n\n'
        '<b>Акция в честь старта сервиса!</b>\n'
        'Тарификация фиксированная на все виды услуг (<b>до 30 сентября 2026</b>)\n\n'
        '<b>Базовый тариф</b>\n'
        f'Фиксированная цена за один вынос: <b>{once_price}₽</b> (до 5кг)\n'
        f'Фиксированная цена за вынос крупногабаритного груза (КГМ): '
        f'<b>{large_order_per_kg}₽</b> за каждый килограмм свыше 5 кг.\n'
        '(Максимальный вес: до 30 кг)\n\n'
        '📦 Месячная подписка <b>«Пакет в день»</b>\n'
        f'<b>{sub_price}₽</b> / месяц — вынос по подписке от '
        f'<b>{sub_price // 31}₽</b> (Вес: до 5 кг)\n\n'
        '📦 Месячная подписка <b>«Крупногабарит»</b>\n'
        f'<b>{large_price}₽</b> / месяц — вынос по подписке от '
        f'<b>{large_price // 31}₽</b> (Вес: до 30 кг).\n\n'
        'Оформи месячную подписку и на ежедневной основе курьер будет забирать Ваш мусор.\n\n'
        '‼️ Просим обратить внимание на вынос крупногабаритного мусора. '
        'Курьеры работают в одиночку, в связи с этим максимальный вес мусора '
        '<b>не должен превышать 30 кг</b>, если вес или габариты мусора будут не доступны к транспортировке '
        'одним курьером, <b>заказ будет отклонен.</b>'
    )

    if subscribed_regular:
        text += f"\n✅ «Пакет в день» активна до {user.subscription_until.strftime('%d.%m.%Y')}"

    if subscribed_large:
        text += f"\n✅ «Крупногабарит» активна до {user.subscription_until_large.strftime('%d.%m.%Y')}"

    await message.answer(
        text,
        parse_mode='html',
        reply_markup=get_tariffs_keyboard(subscribed_regular, subscribed_large),
    )


@router.callback_query(F.data == 'tariffs')
async def process_tariffs_inline(callback: CallbackQuery):
    with SessionLocal() as session:
        once_price = get_price(session, 'single_order')
        sub_price = get_price(session, 'subscription_month')
        large_price = get_price(session, 'large_subscription')
        large_order_per_kg = get_price(session, 'large_order_per_kg')
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        subscribed_regular = has_active_subscription(user)
        subscribed_large = has_active_large_subscription(user)

    text = (
        '💰 <b>Тарифы и подписки сервиса</b>\n\n'
        '<b>Акция в честь старта сервиса!</b>\n'
        'Тарификация фиксированная на все виды услуг (<b>до 30 сентября 2026</b>)\n\n'
        '<b>Базовый тариф</b>\n'
        f'Фиксированная цена за один вынос: <b>{once_price}₽</b> (до 5кг)\n'
        f'Фиксированная цена за вынос крупногабаритного груза (КГМ): '
        f'<b>{large_order_per_kg}₽</b> за каждый килограмм свыше 5 кг.\n'
        '(Максимальный вес: до 30 кг)\n\n'
        '📦 Месячная подписка <b>«Пакет в день»</b>\n'
        f'<b>{sub_price}₽</b> / месяц — вынос по подписке от '
        f'<b>{sub_price // 31}₽</b> (Вес: до 5 кг)\n\n'
        '📦 Месячная подписка <b>«Крупногабарит»</b>\n'
        f'<b>{large_price}₽</b> / месяц — вынос по подписке от '
        f'<b>{large_price // 31}₽</b> (Вес: до 30 кг).\n\n'
        'Оформи месячную подписку и на ежедневной основе курьер будет забирать Ваш мусор.\n\n'
        '‼️ Просим обратить внимание на вынос крупногабаритного мусора. '
        'Курьеры работают в одиночку, в связи с этим максимальный вес мусора '
        '<b>не должен превышать 30 кг</b>, если вес или габариты мусора будут не доступны к транспортировке '
        'одним курьером, <b>заказ будет отклонен.</b>'
    )

    if subscribed_regular:
        text += f"\n✅ «Пакет в день» активна до {user.subscription_until.strftime('%d.%m.%Y')}"

    if subscribed_large:
        text += f"\n✅ «Крупногабарит» активна до {user.subscription_until_large.strftime('%d.%m.%Y')}"

    await callback.message.answer(
        text,
        parse_mode='html',
        reply_markup=get_tariffs_keyboard(subscribed_regular, subscribed_large),
    )

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
        title="Подписка «Пакет в день»",
        description="Безлимитный вынос мусора на 30 дней",
        payload="subscription_payment",
        provider_token=YOOKASSA_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Подписка на месяц", amount=sub_price * 100)],
        need_phone_number=True,
        send_phone_number_to_provider=True,
        provider_data=provider_data,
    )

    await callback.answer()


@router.callback_query(F.data == "buy_large_subscription")
async def buy_large_subscription(callback: CallbackQuery):
    with SessionLocal() as session:
        large_price = get_price(session, "large_subscription")

    provider_data = json.dumps({
        "receipt": {
            "items": [
                {
                    "description": "Подписка «Крупногабарит» на месяц",
                    "quantity": "1.00",
                    "amount": {"value": f"{large_price:.2f}", "currency": "RUB"},
                    "vat_code": 1
                }
            ]
        }
    })

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Подписка «Крупногабарит» на месяц",
        description="Безлимитный вынос крупногабаритного мусора на 30 дней.",
        payload="large_subscription_payment",
        provider_token=YOOKASSA_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Подписка «Крупногабарит»", amount=large_price * 100)],
        need_phone_number=True,
        send_phone_number_to_provider=True,
        provider_data=provider_data,
    )

    await callback.answer()


@router.message(F.text == '📦 Подписка')
async def subscription_status_reply(message: Message):
    with SessionLocal() as session:
        sub_price = get_price(session, "subscription_month")
        large_price = get_price(session, "large_subscription")

        user = session.query(User).filter_by(
            telegram_id=message.from_user.id
        ).first()

        subscribed = has_active_subscription(user)
        subscribed_larged = has_active_large_subscription(user)

        subscription_until = user.subscription_until if subscribed else None
        subscription_until_large = user.subscription_until_large if subscribed_larged else None

    text = "📦 <b>Ваши подписки</b>\n\n"

    if subscribed:
        until = subscription_until.strftime('%d.%m.%Y')
        days_left = (subscription_until - datetime.utcnow()).days + 1

        text += (
            "🗑 <b>«Пакет в день»</b>\n"
            f"✅ Активна\n"
            f"📅 Действует до: <b>{until}</b>\n"
            f"⏳ Осталось дней: <b>{days_left}</b>\n\n"
        )
    else:
        text += (
            "🗑 <b>«Пакет в день»</b>\n"
            "❌ Не активна\n"
            f"💰 Стоимость: <b>{sub_price}₽</b> / месяц\n\n"
        )

    if subscribed_larged:
        until = subscription_until_large.strftime('%d.%m.%Y')
        days_left = (subscription_until_large - datetime.utcnow()).days + 1

        text += (
            "📦 <b>«Крупногабарит»</b>\n"
            f"✅ Активна\n"
            f"📅 Действует до: <b>{until}</b>\n"
            f"⏳ Осталось дней: <b>{days_left}</b>\n"
        )
    else:
        text += (
            "📦 <b>«Крупногабарит»</b>\n"
            "❌ Не активна\n"
            f"💰 Стоимость: <b>{large_price}₽</b> / месяц\n"
        )

    buttons = []

    if not subscribed:
        buttons.append([
            InlineKeyboardButton(
                text="📦 Купить «Пакет в день»",
                callback_data="buy_subscription"
            )
        ])

    if not subscribed_larged:
        buttons.append([
            InlineKeyboardButton(
                text="📦 Купить «Крупногабарит»",
                callback_data="buy_large_subscription"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

    await message.answer(
        text,
        parse_mode='html',
        reply_markup=keyboard,
    )


@router.callback_query(F.data == 'subscription_status')
async def subscription_status_reply(callback: CallbackQuery):
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
            inline_keyboard=[
                [InlineKeyboardButton(text="📦 Купить подписку", callback_data="buy_subscription")]
            ]
        )

        await callback.message.answer(
            f"У вас пока нет подписки.\n\n📦 Месячная подписка — {sub_price}₽",
            reply_markup=keyboard,
        )

    await callback.answer()


@router.callback_query(F.data == 'large_subscription_status')
async def large_subscription_status(callback: CallbackQuery):
    with SessionLocal() as session:
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        subscribed = has_active_large_subscription(user)

    if subscribed:
        until = user.subscription_until_large.strftime('%d.%m.%Y')
        await callback.message.answer(
            f"✅ У вас активна подписка «Крупногабарит» до {until}"
        )
    else:
        with SessionLocal() as session:
            large_price = get_price(session, "large_subscription")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="📦 Купить подписку «Крупногабарит»",
                    callback_data="buy_large_subscription"
                )]
            ]
        )

        await callback.message.answer(
            f"У вас пока нет подписки «Крупногабарит».\n\n"
            f"📦 Месячная подписка — {large_price}₽",
            reply_markup=keyboard,
        )

    await callback.answer()