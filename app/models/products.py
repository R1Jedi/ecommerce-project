import datetime
from decimal import Decimal

from sqlalchemy import Integer, String, Boolean, Numeric, Float, ForeignKey, text, DateTime, func, Computed, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = 'products'
    __table_args__ = (
        Index("ix_products_tsv_gin", "tsv", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0, server_default=text('0'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now,
                                                          server_default=func.now())
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tsv: Mapped[TSVECTOR] = mapped_column(
        TSVECTOR,
        Computed(
            """
            setweight(to_tsvector('english', coalesce(name, '')), 'A')
            || 
            setweight(to_tsvector('english', coalesce(description, '')), 'B')
            """,
            persisted=True,
        ),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('categories.id'), nullable=False)
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    category: Mapped['Category'] = relationship('Category', back_populates='products')
    seller: Mapped['User'] = relationship('User', back_populates='products')
    reviews: Mapped[list['Review']] = relationship('Review', back_populates='product')
    cart_items: Mapped[list["CartItem"]] = relationship("CartItem", back_populates="product",
                                                        cascade="all, delete-orphan")
