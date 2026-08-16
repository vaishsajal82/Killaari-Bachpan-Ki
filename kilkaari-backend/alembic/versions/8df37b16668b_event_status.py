"""add status column to events

Revision ID: 8df37b16668b
Revises: 3152c017fdfd
Create Date: 2026-08-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8df37b16668b'
down_revision: Union[str, None] = '3152c017fdfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'events',
        sa.Column('status', sa.String(length=20), nullable=False, server_default='upcoming'),
    )


def downgrade() -> None:
    op.drop_column('events', 'status')
