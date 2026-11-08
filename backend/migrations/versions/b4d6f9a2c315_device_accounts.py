"""device-based accounts: email and password become optional

Revision ID: b4d6f9a2c315
Revises: a3c5e8f1b204
Create Date: 2026-11-08

Students can start without signing up: the app makes an account tied to
their browser (a long-lived token kept on the device) with no email or
password. Existing email accounts keep working unchanged. Postgres allows
many NULLs under a UNIQUE constraint, so the email index is unaffected.
"""
from alembic import op
import sqlalchemy as sa

revision = 'b4d6f9a2c315'
down_revision = 'a3c5e8f1b204'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('users', 'email', existing_type=sa.String(255), nullable=True)
    op.alter_column('users', 'password_hash', existing_type=sa.String(255), nullable=True)


def downgrade():
    # Device accounts have no email/password; they must be removed first.
    op.execute("DELETE FROM users WHERE email IS NULL OR password_hash IS NULL")
    op.alter_column('users', 'password_hash', existing_type=sa.String(255), nullable=False)
    op.alter_column('users', 'email', existing_type=sa.String(255), nullable=False)
