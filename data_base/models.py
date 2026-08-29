from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

ADMIN_ID = [1097519866, 1473358975, 6511035077]


class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Integer, nullable=False)  # цена в рублях
    label = Column(String, nullable=False)   # человекочитаемое название для админа

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)

    street = Column(String, nullable=True)
    house_number = Column(String, nullable=True)
    entrance = Column(String, nullable=True)
    floor = Column(String, nullable=True)
    room_number = Column(String, nullable=True)

    is_subscribed = Column(Boolean, default=False)
    subscription_until = Column(DateTime, nullable=True)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    order_type = Column(String)          # order_now / order_later
    pickup_time = Column(String, nullable=True)
    street = Column(String)
    house_number = Column(String)
    entrance = Column(String)
    floor = Column(String)
    room_number = Column(String)
    door_or_concierge = Column(String)
    status = Column(String, default="new")  # new / in_progress / done / cancelled
    price = Column(Integer, default=150)
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    admin_messages = Column(String, nullable=True)

    user = relationship("User")