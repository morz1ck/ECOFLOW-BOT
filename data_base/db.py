from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_base.models import Base, User
from typing import Optional
from data_base.models import Price


engine = create_engine("sqlite:///ecoflow.db")
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

def get_or_create_user(session, telegram_id: int, username: Optional[str]):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

DEFAULT_PRICES = {
    "single_order": {"value": 150, "label": "Разовый вынос мусора"},
    "subscription_month": {"value": 1990, "label": "Подписка «Пакет в день»"},
    "large_subscription": {"value": 2990, "label": "Подписка «Крупногабарит»"},
    "large_order_base": {"value": 200, "label": "Крупногабарит, база (до 5 кг)"},
    "large_order_per_kg": {"value": 40, "label": "Доплата за кг свыше 5 кг"},
    }

def init_default_prices():
    with SessionLocal() as session:
        for key, data in DEFAULT_PRICES.items():
            existing = session.query(Price).filter_by(key=key).first()
            if existing is None:
                session.add(Price(key=key, value=data["value"], label=data["label"]))
        session.commit()

init_default_prices()