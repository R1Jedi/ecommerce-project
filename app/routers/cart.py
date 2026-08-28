from decimal import Decimal
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.db_depends import get_async_db, get_product_by_id, get_cart_item
from app.models.cart_items import CartItem as CartItemModel
from app.models.users import User as UserModel
from app.schemas import (
    Cart as CartSchema,
    CartItem as CartItemSchema,
    CartItemCreate,
    CartItemUpdate
)

router = APIRouter(
    prefix="/cart",
    tags=["cart"]
)


@router.get("/", response_model=CartSchema, status_code=status.HTTP_200_OK)
async def get_cart(current_user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    stmt = (
        select(CartItemModel)
        .options(selectinload(CartItemModel.product))
        .where(CartItemModel.user_id == current_user.id)
        .order_by(CartItemModel.id)
    )
    result = await db.scalars(stmt)
    items = result.all()

    total_quantity = sum(item.quantity for item in items)
    price_items = (Decimal(item.quantity) * (item.product.price or Decimal("0")) for item in items)
    total_price = sum(price_items, Decimal("0.00"))

    return CartSchema(
        user_id=current_user.id,
        items=items,
        total_quantity=total_quantity,
        total_price=total_price
    )


@router.post("/items", response_model=CartItemSchema, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(payload: CartItemCreate, current_user: UserModel = Depends(get_current_user),
                           db: AsyncSession = Depends(get_async_db)):
    await get_product_by_id(payload.product_id, db)

    cart_item = await get_cart_item(current_user.id, payload.product_id, db)
    if cart_item:
        cart_item.quantity += payload.quantity
    else:
        cart_item = CartItemModel(
            user_id=current_user.id,
            product_id=payload.product_id,
            quantity=payload.quantity
        )
        db.add(cart_item)

    await db.commit()
    update_item = await get_cart_item(current_user.id, payload.product_id, db)
    return update_item


@router.put("/items/{product_id}", response_model=CartItemSchema, status_code=status.HTTP_200_OK)
async def update_cart_item(product_id: int, payload: CartItemUpdate,
                           current_user: UserModel = Depends(get_current_user),
                           db: AsyncSession = Depends(get_async_db)):
    await get_product_by_id(product_id, db)

    cart_item = await get_cart_item(current_user.id, product_id, db)

    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Товар в корзине не найден")

    cart_item.quantity = payload.quantity
    await db.commit()
    update_item = await get_cart_item(current_user.id, product_id, db)
    return update_item


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_cart(product_id: int, current_user: UserModel = Depends(get_current_user),
                                db: AsyncSession = Depends(get_async_db)):
    cart_item = await get_cart_item(current_user.id, product_id, db)

    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Товар в корзине не найден")

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        db.add(cart_item)
    else:
        await db.delete(cart_item)

    await db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(current_user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    stmt = delete(CartItemModel).where(CartItemModel.user_id == current_user.id)
    await db.execute(stmt)
    await db.commit()
