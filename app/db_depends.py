import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import Depends, HTTPException, status, UploadFile
from pydantic import EmailStr
from sqlalchemy import exists, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category as CategoryModel, Product as ProductModel, User as UserModel, Review as ReviewModel, \
    UserRole, CartItem as CartItemModel, Order as OrderModel, OrderItem as OrderItemModel
from app.database import async_session_maker


# DataBase
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Предоставляет асинхронную сессию SQLAlchemy для работы с базой данных PostgreSQL.
    """
    async with async_session_maker() as session:
        yield session


# Category
async def validate_parent_category(category_id: int | None, db: AsyncSession) -> None:
    """
    Проверяет существование родительской категории по ID.
    """
    if category_id is not None:
        stmt = select(exists().where(CategoryModel.id == category_id, CategoryModel.is_active == True))
        parent_exists = await db.scalar(stmt)

        if not parent_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Родительская категория с ID {category_id} не найдена")


async def get_category_by_id(category_id: int, db: AsyncSession = Depends(get_async_db)) -> CategoryModel:
    """
    Ищет активную категорию по ID. Если не найдена — сразу возвращает 404.
    """
    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True)
    category = await db.scalar(stmt)

    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Категория с ID {category_id} не найдена")
    return category


# Product
async def get_product_by_id(product_id: int, db: AsyncSession = Depends(get_async_db)) -> ProductModel:
    """
    Ищет активный товар по ID. Если не найден — сразу возвращает 404.
    """
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    product = await db.scalar(stmt)

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Товар с ID {product_id} не найден")
    return product


# User
async def get_user_by_id(user_id: int, db: AsyncSession) -> UserModel:
    """
    Ищет активного пользователя по ID. Если не найден — сразу возвращает 404.
    """
    stmt = select(UserModel).where(UserModel.id == user_id, UserModel.is_active == True)
    user = await db.scalar(stmt)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Пользователь с ID {user_id} не найден")
    return user


async def validate_email_exists(email: EmailStr, db: AsyncSession) -> None:
    """
    Проверяет существование email. Если она есть — возвращает 409.
    """
    stmt = select(exists().where(UserModel.email == email, UserModel.is_active == True))
    email_exists = await db.scalar(stmt)

    if email_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Пользователь с email {email} уже зарегистрирован")


async def validate_seller_by_id(seller_id: int, db: AsyncSession) -> None:
    stmt = select(exists().where(UserModel.id == seller_id, UserModel.role == UserRole.seller,
                                 UserModel.is_active == True))
    seller_exists = await db.scalar(stmt)

    if not seller_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Продавец с ID {seller_id} не найден")


# Review
async def get_review_by_id(review_id: int, db: AsyncSession) -> ReviewModel:
    """
    Ищет активный отзыв по ID. Если не найден — сразу возвращает 404.
    """
    stmt = select(ReviewModel).where(ReviewModel.id == review_id, ReviewModel.is_active == True)
    review = await db.scalar(stmt)

    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Отзыв с ID {review_id} не найден")
    return review


async def update_product_rating(product: ProductModel | None, db: AsyncSession):
    """
    Перерасчитывает рейтинг товара
    """
    if product is None:
        return

    stmt = select(func.avg(ReviewModel.grade)).where(ReviewModel.product_id == product.id,
                                                     ReviewModel.is_active == True)
    avg_rating = await db.scalar(stmt) or 0.0
    product.rating = round(float(avg_rating), 1)


# Cart
async def get_cart_item(user_id: int, product_id: int, db: AsyncSession) -> CartItemModel | None:
    stmt = select(CartItemModel).options(selectinload(CartItemModel.product)).where(CartItemModel.user_id == user_id,
                                                                                    CartItemModel.product_id == product_id)
    cart = await db.scalar(stmt)
    return cart


# Order
async def load_order_with_items(order_id: int, db: AsyncSession) -> OrderModel | None:
    stmt = (
        select(OrderModel)
        .options(
            selectinload(OrderModel.items).selectinload(OrderItemModel.product),
        )
        .where(OrderModel.id == order_id)
    )
    order = await db.scalar(stmt)
    return order


# StaticFile
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = BASE_DIR / "media" / "products"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 097 152 байт


async def save_product_image(file: UploadFile) -> str:
    """
    Сохраняет изображение товара и возвращает относительный URL.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Только JPG, PNG или WebP формата")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Изображение слишком большое")

    extension = Path(file.filename or "").suffix.lower() or ".jpg"
    file_name = f"{uuid.uuid4()}{extension}"
    file_path = MEDIA_ROOT / file_name
    file_path.write_bytes(content)

    return f"/media/products/{file_name}"


def remove_product_image(url: str | None) -> None:
    """
    Удаляет файл изображения, если он существует.
    """
    if not url:
        return
    relative_path = url.lstrip("/")
    file_path = BASE_DIR / relative_path
    if file_path.exists():
        file_path.unlink()
