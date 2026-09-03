from fastapi import FastAPI

from app.routers import categories, products, users, reviews, cart, orders, payments
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="FastAPI Интернет-магазин",
    version='0.5.0'
)

# app_v1 = FastAPI(
#     title="FastAPI Интернет-магазин — API v1",
#     version="0.5.0"
# )
#
# app_v1.include_router(categories.router)
# app_v1.include_router(products.router)
# app_v1.include_router(users.router)
# app_v1.include_router(reviews.router)
# app_v1.include_router(cart.router)
# app_v1.include_router(orders.router)
# app_v1.include_router(payments.router)
#
# app.mount("/v1", app_v1)
app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get('/')
async def root():
    """
    Корневой маршрут, подтверждающий, что API работает.
    """
    return {"message": "Добро пожаловать в API интернет-магазина!"}
