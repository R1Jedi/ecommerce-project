from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import SECRET_KEY, ALGORITHM
from app.db_depends import get_async_db
from app.models.users import User as UserModel, UserRole

password_hash = PasswordHash.recommended()

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


def hash_password(password: SecretStr) -> str:
    """
    Преобразует пароль в безопасный хеш.
    """
    return password_hash.hash(password.get_secret_value())


def verify_password(plain_password: SecretStr, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли введённый пароль сохранённому хешу.
    """
    return password_hash.verify(plain_password.get_secret_value(), hashed_password)


def create_access_token(data: dict) -> str:
    """
    Создаёт JWT-токен.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire, 'token_type': 'access'})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Создаёт refresh-токен с длительным сроком действия и token_type='refresh'.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({'exp': expire, 'token_type': 'refresh'})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_user_from_token(token: str, expected_type: str, db: AsyncSession) -> UserModel:
    """
    Внутренняя утилита: проверяет подпись, срок действия,
    тип токена и существование пользователя.
    """
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Не удалось подтвердить учетные данные",
                                          headers={'WWW-Authenticate': 'Bearer'})

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get('sub')
        token_type: str | None = payload.get('token_type')

        if email is None or token_type != expected_type:
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Токен просрочен",
                            headers={'WWW-Authenticate': 'Bearer'})
    except jwt.PyJWTError:
        raise credentials_exception

    stmt = select(UserModel).where(UserModel.email == email, UserModel.is_active == True)
    user = await db.scalar(stmt)

    if user is None:
        raise credentials_exception

    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)) -> UserModel:
    """
    Зависимость для защиты обычных эндпоинтов (требует access-токен).
    """
    return await get_user_from_token(token, expected_type='access', db=db)


async def get_current_seller(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Проверяет, что пользователь имеет роль 'seller'.
    """
    if current_user.role != UserRole.SELLER and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Только продавцы и администраторы имеют доступ")
    return current_user


async def get_current_buyer(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Проверяет, что пользователь имеет роль 'buyer'.
    """
    if current_user.role != UserRole.BUYER and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Только покупатели и администраторы имеют доступ")
    return current_user


async def get_current_admin(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Проверяет, что пользователь является администратором.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Требуются права администратора")
    return current_user
