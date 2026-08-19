import enum

from sqlalchemy import Integer, String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    buyer = "buyer"
    seller = "seller"
    admin = "admin"


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.buyer, nullable=False)  # 'buyer' or 'seller'

    products: Mapped[list['Product']] = relationship('Product', back_populates='seller')
    reviews: Mapped[list['Review']] = relationship('Review', back_populates='user')
