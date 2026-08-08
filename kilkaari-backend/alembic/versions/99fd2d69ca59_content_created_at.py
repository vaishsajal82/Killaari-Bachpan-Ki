"""add created_at to campaigns, testimonials, centers, student_stories

These tables had no timestamp or order column at all, which meant the
public list endpoints (no ORDER BY) could return items in a different,
effectively random order on every request/reload. This adds created_at so
the app can order them deterministically (newest first).

Revision ID: 99fd2d69ca59
Revises: 8df37b16668b
Create Date: 2026-08-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '99fd2d69ca59'
down_revision: Union[str, None] = '8df37b16668b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ["campaigns", "testimonials", "centers", "student_stories"]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, 'created_at')
