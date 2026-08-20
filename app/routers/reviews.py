from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_buyer
from app.db_depends import get_async_db, get_product_by_id, update_product_rating, get_review_by_id
from app.models import Review as ReviewModel, Product as ProductModel, User as UserModel, UserRole
from app.schemas import Review as ReviewSchema, ReviewCreate

router = APIRouter(
    prefix='/reviews',
    tags=['reviews']
)


@router.get("/", response_model=list[ReviewSchema], status_code=status.HTTP_200_OK)
async def get_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Получение всех отзывов
    """
    stmt = select(ReviewModel).join(ProductModel).join(UserModel).where(ReviewModel.is_active == True,
                                                                        ProductModel.is_active == True,
                                                                        UserModel.is_active == True)
    result = await db.scalars(stmt)
    reviews = result.all()
    return reviews


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
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


@router.delete("/{review_id}", status_code=status.HTTP_200_OK)
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
