"""device links: one-time codes to open a profile on another device

Revision ID: c7e1a4d8b952
Revises: b4d6f9a2c315
Create Date: 2026-11-08
"""
from alembic import op
import sqlalchemy as sa

revision = 'c7e1a4d8b952'
down_revision = 'b4d6f9a2c315'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'device_links',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_device_links_user_id', 'device_links', ['user_id'])
    op.create_index('ix_device_links_code_hash', 'device_links', ['code_hash'], unique=True)


def downgrade():
    op.drop_index('ix_device_links_code_hash', table_name='device_links')
    op.drop_index('ix_device_links_user_id', table_name='device_links')
    op.drop_table('device_links')
