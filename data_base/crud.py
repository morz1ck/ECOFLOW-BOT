from data_base.models import Price
from datetime import datetime


def get_price(session, key: str) -> int:
    price = session.query(Price).filter_by(key=key).first()
    if price is None:
        raise ValueError(f"Цена с ключом '{key}' не найдена в БД")
    return price.value


def set_price(session, key: str, new_value: int):
    price = session.query(Price).filter_by(key=key).first()
    if price is None:
        raise ValueError(f"Цена с ключом '{key}' не найдена в БД")
    price.value = new_value
    session.commit()


def get_all_prices(session):
    return session.query(Price).all()

def has_active_subscription(user) -> bool:
    if user is None:
        return False
    return bool(
        user.is_subscribed
        and user.subscription_until
        and user.subscription_until > datetime.utcnow()
    )

def has_saved_address(user) -> bool:
    return all([
        user.street,
        user.house_number,
        user.entrance,
        user.floor,
        user.room_number,
    ])


def has_active_large_subscription(user) -> bool:
    if user is None:
        return False
    return bool(
        user.is_subscribed_large
        and user.subscription_until_large
        and user.subscription_until_large > datetime.utcnow()
    )


def calculate_order_price(session, data: dict, subscribed_regular: bool, subscribed_large: bool):
    """Возвращает (price: float, is_free: bool)"""
    trash_type = data.get("trash_type", "regular")

    if trash_type == "large":
        if subscribed_large:
            return 0.0, True
        base = get_price(session, "large_order_base")
        per_kg = get_price(session, "large_order_per_kg")
        weight = data["weight"]
        extra = max(0.0, weight - 5) * per_kg
        return round(base + extra, 2), False

    if subscribed_regular:
        return 0.0, True
    return float(get_price(session, "single_order")), False