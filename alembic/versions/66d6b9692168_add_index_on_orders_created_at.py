"""add index on orders.created_at

Revision ID: 66d6b9692168
Revises: 0299ee7ccdcd
Create Date: 2026-05-18 23:08:00.364218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66d6b9692168'
down_revision: Union[str, None] = '0299ee7ccdcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('idx_orders_created_at', 'orders', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_orders_created_at', 'orders')
