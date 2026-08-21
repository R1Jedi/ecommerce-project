import datetime

from pydantic import BaseModel, Field, ConfigDict, EmailStr, SecretStr
from decimal import Decimal
from typing import Annotated, Literal

from app.models.users import UserRole


# Category
class CategoryCreate(BaseModel):
    """
    Модель для создания и обновления категории.
    Используется в POST и PUT запросах.
    """
    name: Annotated[str, Field(min_length=3, max_length=50,
                               description="Название категории (3-50 символов)")]
    parent_id: Annotated[int | None, Field(default=None, description="ID родительской категории, если есть")]


class Category(CategoryCreate):
    """
    Модель для ответа с данными категории.
    Используется в GET-запросах.
    """
    id: Annotated[int, Field(description="Уникальный идентификатор категории")]
    is_active: Annotated[bool, Field(description="Активность категории")]

    model_config = ConfigDict(from_attributes=True)


# Product
class ProductCreate(BaseModel):
    """
    Модель для создания и обновления товара.
    Используется в POST и PUT запросах.
    """
    name: Annotated[str, Field(min_length=3, max_length=100,
                               description="Название товара (3-100 символов)")]
    description: Annotated[str | None, Field(default=None, max_length=500,
                                             description="Описание товара (до 500 символов)")]
    price: Annotated[Decimal, Field(gt=0, description="Цена товара (больше 0)", decimal_places=2)]
    image_url: Annotated[str | None, Field(default=None, max_length=200, description="URL изображения товара")]
    stock: Annotated[int, Field(ge=0, description="Количество товара на складе (0 или больше)")]
    category_id: Annotated[int, Field(description="ID категории, к которой относится товар")]


class Product(ProductCreate):
    """
    Модель для ответа с данными товара.
    Используется в GET-запросах.
    """
    id: Annotated[int, Field(description="Уникальный идентификатор товара")]
    rating: Annotated[float, Field(description="Рейтинг товара")]
    is_active: Annotated[bool, Field(description="Активность товара")]

    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    """
    Список пагинации для товаров
    """
    items: Annotated[list[Product], Field(description="Товары для текущей страницы")]
    total: Annotated[int, Field(ge=0, description="Общее количество товаров")]
    page: Annotated[int, Field(ge=1, description="Номер текущей страницы")]
    page_size: Annotated[int, Field(ge=1, description="Количество элементов на странице")]

    model_config = ConfigDict(from_attributes=True)


# User
class UserBase(BaseModel):
    """
    Базовая модель с общими полями для пользователя.
    Сама по себе в роутерах не используется.
    """
    email: Annotated[EmailStr, Field(description="Email пользователя")]


class UserCreate(UserBase):
    """
    Модель для создания и обновления пользователя.
    Используется в POST и PUT запросах.
    """
    password: Annotated[SecretStr, Field(min_length=8, description="Пароль (минимум 8 символов)")]
    role: Annotated[Literal[UserRole.buyer, UserRole.seller], Field(default=UserRole.buyer, description="Роль пользователя")]


class User(UserBase):
    """
    Модель для ответа с данными пользователя.
    Используется в GET-запросах.
    """
    id: Annotated[int, Field(description="Уникальный идентификатор пользователя")]
    is_active: Annotated[bool, Field(description="Активность пользователя")]
    role: Annotated[UserRole, Field(description="Текущая роль пользователя")]

    model_config = ConfigDict(from_attributes=True)


# Tokens
class RefreshTokenRequest(BaseModel):
    """
    Модель для валидации токена
    """
    refresh_token: str


# Review
class ReviewBase(BaseModel):
    """
    Базовая модель с общими полями для обзоров.
    Сама по себе в роутерах не используется.
    """
    grade: Annotated[int, Field(ge=1, le=5, description='Оценка товара от 1 до 5 включительно')]
    comment: Annotated[str | None, Field(default=None, description='Комментарий к отзыву о товаре')]


class ReviewCreate(ReviewBase):
    """
    Модель для создания отзыва.
    Используется в POST-запросах.
    """
    product_id: Annotated[int, Field(description='Уникальный идентификатор товара')]


class Review(ReviewBase):
    """
    Модель для ответа с данными отзыва.
    Используется в GET-запросах.
    """
    id: Annotated[int, Field(description="Уникальный идентификатор отзыва")]
    user_id: Annotated[int, Field(description="Уникальный идентификатор пользователя")]
    product_id: Annotated[int, Field(description="Уникальный идентификатор товара")]
    comment_date: Annotated[datetime.datetime, Field(description="Дата создания отзыва")]
    is_active: Annotated[bool, Field(description="Активность отзыва")]

    model_config = ConfigDict(from_attributes=True)
