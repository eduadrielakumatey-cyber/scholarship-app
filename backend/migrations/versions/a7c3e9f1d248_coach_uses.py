"""essay coach: one row per AI feedback request (daily limit)

Revision ID: a7c3e9f1d248
Revises: f5b2d8e4a613
Create Date: 2026-11-10
"""
from alembic import op
import sqlalchemy as sa

revision = 'a7c3e9f1d248'
down_revision = 'f5b2d8e4a613'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'coach_uses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_coach_uses_user_id', 'coach_uses', ['user_id'])
    op.create_index('ix_coach_uses_created_at', 'coach_uses', ['created_at'])


def downgrade():
    op.drop_index('ix_coach_uses_created_at', table_name='coach_uses')
    op.drop_index('ix_coach_uses_user_id', table_name='coach_uses')
    op.drop_table('coach_uses')
