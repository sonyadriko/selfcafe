"""remove staff role from users

Revision ID: b72435dde5b6
Revises: 47b66818c7b7
Create Date: 2026-05-30 17:12:55.911342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b72435dde5b6'
down_revision: Union[str, None] = '47b66818c7b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE users SET role = 'kasir' WHERE role = 'staff'")
    op.alter_column('users', 'role',
        existing_type=sa.Enum('admin', 'staff', 'kasir'),
        type_=sa.Enum('admin', 'kasir'),
        nullable=False
    )


def downgrade() -> None:
    op.alter_column('users', 'role',
        existing_type=sa.Enum('admin', 'kasir'),
        type_=sa.Enum('admin', 'staff', 'kasir'),
        nullable=False
    )
