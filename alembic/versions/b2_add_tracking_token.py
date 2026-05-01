"""Add tracking token to orders

Revision ID: b2_add_tracking_token
Revises: aeb3ad57d02d
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = 'b2_add_tracking_token'
down_revision: Union[str, None] = 'aeb3ad57d02d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tracking_token column to orders table
    op.add_column('orders',
        sa.Column('tracking_token', sa.String(length=36), nullable=False, server_default='00000000-0000-0000-0000-000000000000')
    )

    # Generate unique tokens for existing orders
    connection = op.get_bind()
    orders = connection.execute(sa.text("SELECT id FROM orders WHERE tracking_token = '00000000-0000-0000-0000-000000000000'"))

    for order in orders:
        new_token = str(uuid.uuid4())
        connection.execute(
            sa.text("UPDATE orders SET tracking_token = :token WHERE id = :order_id"),
            {"token": new_token, "order_id": order[0]}
        )

    # Make the column unique and add index
    op.create_index('ix_orders_tracking_token', 'orders', ['tracking_token'], unique=True)
    op.alter_column('orders', 'tracking_token', nullable=False, server_default=None)


def downgrade() -> None:
    op.drop_index('ix_orders_tracking_token', table_name='orders')
    op.drop_column('orders', 'tracking_token')
