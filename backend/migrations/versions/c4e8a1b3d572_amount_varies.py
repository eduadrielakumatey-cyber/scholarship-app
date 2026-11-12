"""amount varies: college funds that don't publish a fixed award amount

Revision ID: c4e8a1b3d572
Revises: b8d4f2a6c917
Create Date: 2026-11-11
"""
from alembic import op
import sqlalchemy as sa

revision = 'c4e8a1b3d572'
down_revision = 'b8d4f2a6c917'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scholarships', sa.Column('amount_varies', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('scholarships', 'amount_varies')
