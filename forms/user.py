from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    time = State()
    street = State()          # если уже добавляли для улиц
    address_full = State()
    door_or_concierge = State()
    confirm = State()
    new_price = State()       # ← новое, для смены цены