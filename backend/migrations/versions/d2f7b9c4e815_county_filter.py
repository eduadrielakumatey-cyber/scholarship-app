"""county filter: awards limited to one Maryland county, and each student's county

Revision ID: d2f7b9c4e815
Revises: c4e8a1b3d572
Create Date: 2026-11-22

scholarships.counties -- Maryland counties whose students can win ([] = any).
users.county          -- the student's home county (NULL = not answered, so
                         county-only awards stay hidden).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = 'd2f7b9c4e815'
down_revision = 'c4e8a1b3d572'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scholarships', sa.Column('counties', ARRAY(sa.String()), nullable=False, server_default='{}'))
    op.add_column('users', sa.Column('county', sa.String(length=40), nullable=True))


def downgrade():
    op.drop_column('users', 'county')
    op.drop_column('scholarships', 'counties')
