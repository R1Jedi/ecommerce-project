from datetime import datetime, date

from pydantic import BaseModel, Field, ConfigDict, EmailStr, SecretStr
from decimal import Decimal
from typing import Annotated, Literal

from app.models.users import UserRole


# Category
class CategoryCreate(BaseModel):
    """
    Модель для создания и обновления категории.
    """
    name: Annotated[str, Field(min_length=3, max_length=50,
                               description="Название категории (3-50 символов)")]
    parent_id: Annotated[int | None, Field(default=None, description="ID родительской категории, если есть")]


class Category(CategoryCreate):
    """
    Модель для ответа с данными категории.
    """
    id: Annotated[int, Field(description="Уникальный идентификатор категории")]
    is_active: Annotated[bool, Field(description="Активность категории")]

    model_config = ConfigDict(from_attributes=True)


# Product
class ProductCreate(BaseModel):
    """
    Модель для создания и обновления товара.
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
    """
    id: Annotated[int, Field(description="Уникальный идентификатор товара")]
    rating: Annotated[float, Field(description="Рейтинг товара")]
    is_active: Annotated[bool, Field(description="Активность товара")]
    created_at: Annotated[datetime, Field(description="Дата добавления товара")]
    updated_at: Annotated[datetime | None, Field(default=None, description="Дата обновления товара")]

    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    """
    Список пагинации для товаров.
    """
    items: Annotated[list[Product], Field(description="Товары для текущей страницы")]
    total: Annotated[int, Field(ge=0, description="Общее количество товаров")]
    page: Annotated[int, Field(ge=1, description="Номер текущей страницы")]
    page_size: Annotated[int, Field(ge=1, description="Количество элементов на странице")]

    model_config = ConfigDict(from_attributes=True)


class ProductFilter(BaseModel):
    """
    Фильтры для пагинации товаров.
    """
    page: Annotated[int, Field(default=1, ge=1, description="Номер страницы")]
    page_size: Annotated[int, Field(default=20, ge=1, le=100, description="Размер страницы")]
    search: Annotated[str | None, Field(default=None, min_length=1, description="Поиск по названию товара")]
    category_id: Annotated[int | None, Field(default=None, description="Поиск товара по категории")]
    min_price: Annotated[float | None, Field(default=None, ge=0, description="Минимальная цена товара")]
    max_price: Annotated[float | None, Field(default=None, ge=0, description="Максимальная цена товара")]
    in_stock: Annotated[bool | None, Field(default=None, description="Есть ли товар в наличии")]
    seller_id: Annotated[int | None, Field(default=None, description="Поиск товара по продавцу")]
    created_after: Annotated[date | None, Field(default=None,
                                                description="Искать товары, добавленные начиная с этой даты")]
    created_before: Annotated[date | None, Field(default=None,
                                                 description="Искать товары, добавленные до этой даты")]


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
    """
    password: Annotated[SecretStr, Field(min_length=8, description="Пароль (минимум 8 символов)")]
    role: Annotated[
        Literal[UserRole.buyer, UserRole.seller], Field(default=UserRole.buyer, description="Роль пользователя")]


class User(UserBase):
    """
    Модель для ответа с данными пользователя.
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
    """
    product_id: Annotated[int, Field(description='Уникальный идентификатор товара')]


class Review(ReviewBase):
    """
    Модель для ответа с данными отзыва.
    """
    id: Annotated[int, Field(description="Уникальный идентификатор отзыва")]
    user_id: Annotated[int, Field(description="Уникальный идентификатор пользователя")]
    product_id: Annotated[int, Field(description="Уникальный идентификатор товара")]
    comment_date: Annotated[datetime, Field(description="Дата создания отзыва")]
    is_active: Annotated[bool, Field(description="Активность отзыва")]

    model_config = ConfigDict(from_attributes=True)


# CartItem
class CartItemBase(BaseModel):
    """
    Базовая модель с общими полями для корзин.
    Сама по себе в роутерах не используется.
    """
    product_id: int = Field(description="ID товара")
    quantity: int = Field(ge=1, description="Количество товара")


class CartItemCreate(CartItemBase):
    """Модель для добавления нового товара в корзину."""
    pass


class CartItemUpdate(BaseModel):
    """Модель для обновления количества товара в корзине."""
    quantity: int = Field(ge=1, description="Новое количество товара")


class CartItem(BaseModel):
    """Товар в корзине с данными продукта."""
    id: int = Field(description="ID позиции корзины")
    quantity: int = Field(ge=1, description="Количество товара")
    product: Product = Field(description="Информация о товаре")

    model_config = ConfigDict(from_attributes=True)


class Cart(BaseModel):
    """Полная информация о корзине пользователя."""
    user_id: int = Field(description="ID пользователя")
    items: list[CartItem] = Field(default_factory=list, description="Содержимое корзины")
    total_quantity: int = Field(ge=0, description="Общее количество товаров")
    total_price: Decimal = Field(ge=0, description="Общая стоимость товаров")

    model_config = ConfigDict(from_attributes=True)
