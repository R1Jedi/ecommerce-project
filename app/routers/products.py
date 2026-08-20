from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_seller
from app.db_depends import get_async_db, get_product_by_id, get_category_by_id
from app.models import Category as CategoryModel, Product as ProductModel, User as UserModel, Review as ReviewModel
from app.schemas import Product as ProductSchema, ProductCreate, Review as ReviewSchema

router = APIRouter(
    prefix='/products',
    tags=['products']
)


@router.get("/", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех товаров.
    """
    stmt = select(ProductModel).join(CategoryModel).where(ProductModel.is_active == True,
                                                          CategoryModel.is_active == True,
                                                          ProductModel.stock > 0)
    result = await db.scalars(stmt)
    products = result.all()
    return products


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


@router.get("/category/{category_id}", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    await get_category_by_id(category_id, db)

    stmt = select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active == True)
    result = await db.scalars(stmt)
    products = result.all()
    return products


@router.get("/{product_id}/reviews", response_model=list[ReviewSchema], status_code=status.HTTP_200_OK)
async def get_reviews_by_product_id(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Получение всех отзывов о конкретном товаре
    """
    await get_product_by_id(product_id, db=db)

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

    if product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Вы можете редактировать только свои товары")

    stmt = update(ProductModel).where(ProductModel.id == product.id).values(**product_updated.model_dump())
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
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Вы можете удалять только свои товары")

    product.is_active = False
    await db.commit()
    return {"status": "success", "message": "Товар переведен в статус неактивного"}
