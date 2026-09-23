from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.routers import categories, products, users, reviews, cart, orders, payments
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    with logger.contextualize():
        try:
            engine = create_async_engine(settings.database_url, echo=True)
            session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

            app.state.session_maker = session_maker
            yield
        except Exception as e:
            logger.exception(f"Критическая ошибка при запуске приложения: {e}")
            raise e
        finally:
            await engine.dispose()


# Главное приложение
app = FastAPI(
    title="FastAPI Интернет-магазин",
    version='0.5.0',
    lifespan=lifespan
)


# Логи
logger.add("info.log", format="Log: [{extra[log_id]}:{time} - {level} - {message}]", level="INFO", enqueue=True)


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        try:
            response = await call_next(request)
            if response.status_code in [401, 402, 403, 404]:
                logger.warning(f"Request to {request.url.path} failed")
            else:
                logger.info('Successfully accessed ' + request.url.path)
        except Exception as ex:
            logger.error(f"Request to {request.url.path} failed: {ex}")
            response = JSONResponse(content={"success": False}, status_code=500)
        return response

# app_v1 = FastAPI(
#     title="FastAPI Интернет-магазин — API v1",
#     version="0.5.0"
# )

# Подключение ручек
categories.router.include_router(products.router)
app.include_router(categories.router)

app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)

# Привязка медиа
# app.mount("/v1", app_v1)
app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get('/')
async def root():
    """
    Корневой маршрут, подтверждающий, что API работает.
    """
    return {"message": "Добро пожаловать в API интернет-магазина!"}
