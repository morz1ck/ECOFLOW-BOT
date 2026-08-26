from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    time = State()
    street = State()
    address_rest = State()   # переименовано из address_full
    address_confirm = State() 
    door_or_concierge = State()
    confirm = State()
    new_price = State()