from aiogram import Router
from handlers.client.start import router as start_router
from .client.order import router as order_router
from .client.adress import router as address_router
from .client.payment import router as payment_router
from .client.subscription import router as subscription_router
from .admin.order_management import router as admin_order_mgmt_router
from .admin.orders_list import router as admin_orders_list_router
from .admin.prices import router as admin_prices_router
from .admin.broadcast import router as admin_broadcast_router

main_router = Router()
main_router.include_routers(
    start_router,
    order_router,
    address_router,
    payment_router,
    subscription_router,
    admin_order_mgmt_router,
    admin_orders_list_router,
    admin_prices_router,
    admin_broadcast_router,
)