from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_seller
from app.db_depends import get_async_db, get_product_by_id, get_category_by_id, validate_seller_by_id
from app.models import Product as ProductModel, User as UserModel, Review as ReviewModel, UserRole
from app.schemas import Product as ProductSchema, ProductCreate, Review as ReviewSchema, ProductList, ProductFilter

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/", response_model=ProductList, status_code=status.HTTP_200_OK)
async def get_all_products(request: Annotated[ProductFilter, Query()], db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех товаров с поддержкой фильтров.
    """
    # Проверка логики min_price <= max_price
    if request.min_price is not None and request.max_price is not None and request.min_price > request.max_price:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="min_price не может быть больше max_price")

    # Формируем список фильтров
    filters = [ProductModel.is_active == True]

    if request.search is not None:
        search_value = request.search.strip()
        if search_value:
            filters.append(ProductModel.name.ilike(f"%{search_value}%"))
    if request.category_id is not None:
        await get_category_by_id(request.category_id, db)
        filters.append(ProductModel.category_id == request.category_id)
    if request.min_price is not None:
        filters.append(ProductModel.price >= request.min_price)
    if request.max_price is not None:
        filters.append(ProductModel.price <= request.max_price)
    if request.in_stock is not None:
        filters.append(ProductModel.stock > 0 if request.in_stock else ProductModel.stock == 0)
    if request.seller_id is not None:
        await validate_seller_by_id(request.seller_id, db)
        filters.append(ProductModel.seller_id == request.seller_id)
    if request.created_after is not None:
        filters.append(ProductModel.created_at >= request.created_after)
    if request.created_before is not None:
        filters.append(ProductModel.created_at <= request.created_before)

    # Подсчёт общего количества с учётом фильтров
    stmt = select(func.count(ProductModel.id)).where(*filters)
    total = await db.scalar(stmt) or 0

    # Выборка товаров с фильтрами и пагинацией
    stmt = (
        select(ProductModel)
        .where(*filters)
        .order_by(ProductModel.id)
        .offset((request.page - 1) * request.page_size)
        .limit(request.page_size)
    )
    result = await db.scalars(stmt)
    items = result.all()
    return {
        "items": items,
        "total": total,
        "page": request.page,
        "page_size": request.page_size
    }


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_async_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
    Создаёт новый товар.
    """
    await get_category_by_id(product.category_id, db)

    new_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


@router.get("/{product_id}/reviews", response_model=list[ReviewSchema], status_code=status.HTTP_200_OK)
async def get_reviews_by_product_id(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Получение всех отзывов о конкретном товаре
    """
    await get_product_by_id(product_id, db)

    stmt = select(ReviewModel).join(UserModel).where(ReviewModel.product_id == product_id,
                                                     ReviewModel.is_active == True,
                                                     UserModel.is_active == True)
    result = await db.scalars(stmt)
    reviews = result.all()
    return reviews


@router.get("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def get_product(product: ProductModel = Depends(get_product_by_id),
                      db: AsyncSession = Depends(get_async_db)) -> ProductModel:
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    await get_category_by_id(product.category_id, db)
    return product


@router.put("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def update_product(product_updated: ProductCreate, product: ProductModel = Depends(get_product_by_id),
                         current_user: UserModel = Depends(get_current_seller),
                         db: AsyncSession = Depends(get_async_db)) -> ProductModel:
    """
    Обновляет товар по его ID.
    """
    await get_category_by_id(product_updated.category_id, db)

    if product.seller_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Вы можете редактировать только свои товары")

    stmt = update(ProductModel).where(ProductModel.id == product.id).values(**product_updated.model_dump(),
                                                                            updated_at=func.now())
    await db.execute(stmt)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product: ProductModel = Depends(get_product_by_id),
                         current_user: UserModel = Depends(get_current_seller),
                         db: AsyncSession = Depends(get_async_db)) -> dict:
    """
    Удаляет товар по его ID
    """
    if product.seller_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Вы можете удалять только свои товары")

    product.is_active = False
    await db.commit()
    return {"status": "success", "message": "Товар переведен в статус неактивного"}
