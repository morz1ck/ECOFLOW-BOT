from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton)

STREETS = ['ул. Голландская', 'ул. Ясная', 'ул. Тюльпанов']


def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗑 Вынести мусор сейчас")],
            [KeyboardButton(text="🕐 Заказать на время")],
            [KeyboardButton(text="📦 Мои заказы")],
            [KeyboardButton(text="ℹ️ Как это работает")],
            [KeyboardButton(text="💰 Тарифы")],
            [KeyboardButton(text="📦 Подписка")]
        ], resize_keyboard=True, input_field_placeholder='Выберите действие...'
    )


def get_main_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Вынести мусор сейчас", callback_data="order_now")],
            [InlineKeyboardButton(text="🕐 Заказать на время", callback_data="order_later")],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="ℹ️ Как это работает", callback_data="how_it_works")],
            [InlineKeyboardButton(text='💰 Тарифы', callback_data='tariffs')],
            [InlineKeyboardButton(text='📦 Подписка', callback_data='subscription_status')],
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
        inline_keyboard=[[InlineKeyboardButton(text="Отменить", callback_data="cancel")],])


def get_orders_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚚 Активные заказы", callback_data="admin_orders:active")],
            [InlineKeyboardButton(text="✅ Завершённые заказы", callback_data="admin_orders:done")],
        ]
    )


def get_trash_type_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Обычный мусор", callback_data="trash_regular")],
            [InlineKeyboardButton(text="📦 Крупногабаритный", callback_data="trash_large")],
        ]
    )

def get_tariffs_keyboard(subscribed_regular: bool, subscribed_large: bool):
    buttons = []
    if not subscribed_regular:
        buttons.append([InlineKeyboardButton(text="📦 Оформить «Пакет в день»", callback_data="buy_subscription")])
    if not subscribed_large:
        buttons.append([InlineKeyboardButton(text="🛋 Оформить «Крупногабарит»", callback_data="buy_large_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

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

def get_tariffs_keyboard(subscribed_regular, subscribed_large):

    buttons = []

    if subscribed_regular:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Обычный мусор — подписка активна",
                callback_data="subscription_status"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="📦 Подписка на обычный мусор",
                callback_data="buy_subscription"
            )
        ])

    if subscribed_large:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Крупный мусор — подписка активна",
                callback_data="large_subscription_status"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="📦 Подписка на крупный мусор",
                callback_data="buy_large_subscription"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_change_prices_keyboard(prices):
    buttons = []
    for p in prices:
        buttons.append([InlineKeyboardButton(text=f"{p.label}: {p.value}₽", callback_data=f"changeprice:{p.key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)