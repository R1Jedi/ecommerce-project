from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy import exists, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category as CategoryModel, Product as ProductModel, User as UserModel, Review as ReviewModel
from app.database import async_session_maker


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Предоставляет асинхронную сессию SQLAlchemy для работы с базой данных PostgreSQL.
    """
    async with async_session_maker() as session:
        yield session


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


async def validate_email_exists(email: EmailStr, db: AsyncSession) -> None:
    """
    Проверяет существование email. Если она есть — возвращает 409.
    """
    stmt = select(exists().where(UserModel.email == email, UserModel.is_active == True))
    email_exists = await db.scalar(stmt)

    if email_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Пользователь с email {email} уже зарегистрирован")


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
