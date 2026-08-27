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