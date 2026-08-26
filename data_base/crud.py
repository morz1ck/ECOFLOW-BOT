from data_base.models import Price

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

def has_saved_address(user) -> bool:
    return all([
        user.street,
        user.house_number,
        user.entrance,
        user.floor,
        user.room_number,
    ])