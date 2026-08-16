"""add cloudinary_public_id to gallery_items

Supports the Cloudinary image storage migration: lets the app delete the
old Cloudinary asset when a gallery item's image is replaced or the item
itself is deleted, instead of orphaning it. Nullable — existing rows (with
either an old locally-hosted URL or a manually-pasted external URL) simply
have no public_id, which is fine; cleanup is skipped for those and their
image_url keeps working exactly as before.

Revision ID: b06874b62aef
Revises: 99fd2d69ca59
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b06874b62aef'
down_revision: Union[str, None] = '99fd2d69ca59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'gallery_items',
        sa.Column('cloudinary_public_id', sa.String(length=300), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('gallery_items', 'cloudinary_public_id')
