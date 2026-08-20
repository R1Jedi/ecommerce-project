"""fix_user_role_case

Revision ID: 91c1ca06b6fe
Revises: 15fc894b3c37
Create Date: 2026-08-20 09:35:15.167018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91c1ca06b6fe'
down_revision: Union[str, Sequence[str], None] = '15fc894b3c37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Меняем тип колонки на обычную строку, чтобы разорвать связь со старым типом Enum
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50);")

    # 2. Переводим все старые заглавные роли (BUYER, SELLER) в нижний регистр (buyer, seller)
    op.execute("UPDATE users SET role = LOWER(role);")

    # 3. Удаляем старый системный тип Postgres, в котором были большие буквы
    # Примечание: если имя типа в БД отличается, Postgres выдаст ошибку.
    # Если упадет, замените 'userrole' на фактическое имя (обычно имя вашего Enum класса в нижнем регистре).
    op.execute("DROP TYPE IF EXISTS userrole;")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50);")
