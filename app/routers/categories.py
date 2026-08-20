from fastapi import APIRouter, Depends, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.db_depends import get_async_db, validate_parent_category, get_category_by_id
from app.models import Category as CategoryModel, User as UserModel, UserRole
from app.schemas import Category as CategorySchema, CategoryCreate

router = APIRouter(
    prefix='/categories',
    tags=['categories']
)


@router.get("/", response_model=list[CategorySchema], status_code=status.HTTP_200_OK)
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех категорий товаров.
    """
    stmt = select(CategoryModel).where(CategoryModel.is_active == True)
    result = await db.scalars(stmt)
    categories = result.all()
    return categories


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, current_user: UserModel = Depends(get_current_admin),
                          db: AsyncSession = Depends(get_async_db)) -> CategoryModel:
    """
    Создаёт новую категорию.
    """
    await validate_parent_category(category.parent_id, db)

    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    await db.commit()
    return db_category


@router.put("/{category_id}", response_model=CategorySchema, status_code=status.HTTP_200_OK)
async def update_category(category_updated: CategoryCreate, db_category: CategoryModel = Depends(get_category_by_id),
                          current_user: UserModel = Depends(get_current_admin),
                          db: AsyncSession = Depends(get_async_db)) -> CategoryModel:
    """ Обновляет категорию по её ID. """
    await validate_parent_category(category_updated.parent_id, db)

    stmt = update(CategoryModel).where(CategoryModel.id == db_category.id).values(**category_updated.model_dump())
    await db.execute(stmt)
    await db.commit()
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category: CategoryModel = Depends(get_category_by_id),
                          current_user: UserModel = Depends(get_current_admin),
                          db: AsyncSession = Depends(get_async_db)) -> dict:
    """
    Удаляет категорию по её ID.
    """
    category.is_active = False
    await db.commit()
    return {"status": "success", "message": f"Категория с ID {category.id} успешно деактивирована"}
