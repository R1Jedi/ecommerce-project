from typing import Annotated

from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_buyer
from app.db_depends import get_async_db, get_product_by_id, update_product_rating, get_review_by_id
from app.models import Review as ReviewModel, Product as ProductModel, User as UserModel, UserRole
from app.schemas import Review as ReviewSchema, ReviewCreate, ReviewFilterParams

router = APIRouter(
    prefix="/reviews"
)


@router.get("/", response_model=list[ReviewSchema], status_code=status.HTTP_200_OK, tags=["reviews"])
async def get_reviews(request: Annotated[ReviewFilterParams, Query()], db: AsyncSession = Depends(get_async_db)):
    """
     Получение отзывов с постраничной пагинацией и фильтрацией по товару и оценке
    """
    filters = [ReviewModel.is_active == True, ProductModel.is_active == True, UserModel.is_active == True]

    if request.product_id is not None:
        await get_product_by_id(request.product_id, db)
        filters.append(ReviewModel.product_id == request.product_id)
    if request.grade is not None:
        filters.append(ReviewModel.grade == request.grade)
    if request.date_from is not None:
        filters.append(ReviewModel.comment_date >= request.date_from)
    if request.date_to is not None:
        filters.append(ReviewModel.comment_date <= request.date_to)

    stmt = (
        select(ReviewModel)
        .join(ProductModel)
        .join(UserModel)
        .where(*filters)
        .order_by(desc(ReviewModel.id))
        .offset((request.page - 1) * request.page_size)
        .limit(request.page_size)
    )

    result = await db.scalars(stmt)
    reviews = result.all()
    return reviews


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED, tags=["reviews"])
async def create_review(review: ReviewCreate, current_user: UserModel = Depends(get_current_buyer),
                        db: AsyncSession = Depends(get_async_db)):
    """
    Добавление отзыва
    """
    if current_user.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Администраторы не могут оставлять отзывы к товарам")
    product = await get_product_by_id(review.product_id, db)

    new_review = ReviewModel(**review.model_dump(), user_id=current_user.id)
    db.add(new_review)

    try:
        await db.flush()
        await update_product_rating(product, db)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Вы уже оставили отзыв на этот товар")

    await db.refresh(new_review)
    return new_review


@router.delete("/{review_id}", status_code=status.HTTP_200_OK, tags=["reviews"])
async def delete_review(review_id: int, current_user: UserModel = Depends(get_current_buyer),
                        db: AsyncSession = Depends(get_async_db)) -> dict:
    """
    Мягкое удаление отзыва
    """
    review = await get_review_by_id(review_id, db)

    if current_user.role != UserRole.admin and review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Вы можете удалять только свои отзывы")
    review.is_active = False
    await db.flush()

    product = await db.get(ProductModel, review.product_id)

    if product and product.is_active:
        await update_product_rating(product, db)

    await db.commit()
    return {"message": "Review deleted"}
