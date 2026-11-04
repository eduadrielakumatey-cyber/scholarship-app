"""scholarship essay_required flag

Revision ID: a3c5e8f1b204
Revises: e7b2c4a91f05
Create Date: 2026-11-04

Nullable boolean: True = the application asks for an essay/personal
statement, False = the official page says no essay, NULL = unknown.
"""
from alembic import op
import sqlalchemy as sa

revision = 'a3c5e8f1b204'
down_revision = 'e7b2c4a91f05'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scholarships', sa.Column('essay_required', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('scholarships', 'essay_required')
