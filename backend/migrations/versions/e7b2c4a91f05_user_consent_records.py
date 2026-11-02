"""users consent records (terms acceptance, demographics opt-in)

Revision ID: e7b2c4a91f05
Revises: d9a3f61c8e2b
Create Date: 2026-11-01

Records when a student accepted the Terms/Privacy Policy at signup (and
which version), and when they separately opted in to sharing sensitive
demographic data. Existing rows get NULL: there's no record of consent for
accounts created before this, so the app treats them as not-yet-consented
for demographics and they'll be asked again from the profile screen.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e7b2c4a91f05'
down_revision = 'd9a3f61c8e2b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('terms_accepted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('terms_version', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('demographics_consent_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('users', 'demographics_consent_at')
    op.drop_column('users', 'terms_version')
    op.drop_column('users', 'terms_accepted_at')
