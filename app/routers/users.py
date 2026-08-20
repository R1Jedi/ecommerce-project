from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import hash_password, verify_password, create_access_token, create_refresh_token, get_user_from_token
from app.db_depends import get_async_db, validate_email_exists
from app.models import User as UserModel
from app.schemas import UserCreate, User as UserSchema, RefreshTokenRequest

router = APIRouter(
    prefix='/users',
    tags=['users']
)


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Регистрирует нового пользователя с ролью 'buyer' или 'seller'.
    """
    await validate_email_exists(user.email, db)

    db_user = UserModel(email=user.email, hashed_password=hash_password(user.password), role=user.role)
    db.add(db_user)
    await db.commit()
    return db_user


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_db)):
    """
    Аутентифицирует пользователя и возвращает JWT с email, role и id.
    """
    user = await db.scalar(select(UserModel).where(UserModel.email == form_data.username,
                                                   UserModel.is_active == True))

    if not user or not verify_password(SecretStr(form_data.password), user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Неверный пароль или email",
                            headers={"WWW-Authenticate": "Bearer"})
    data = {"sub": user.email, "role": user.role, "id": user.id}
    access_token = create_access_token(data=data)
    refresh_token = create_refresh_token(data=data)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh-token")
async def refresh_tokens(body: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
    """
    Обновляет refresh-токен, принимая старый refresh-токен в теле запроса.
    """
    user = await get_user_from_token(body.refresh_token, expected_type="refresh", db=db)

    data = {"sub": user.email, "role": user.role, "id": user.id}
    new_access_token = create_access_token(data=data)
    new_refresh_token = create_refresh_token(data=data)
    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
