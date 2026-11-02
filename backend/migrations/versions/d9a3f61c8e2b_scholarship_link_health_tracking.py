"""scholarship link-health tracking (status, last_verified_at, application_url, is_recurring_program)

Revision ID: d9a3f61c8e2b
Revises: d41f2a9c7b3e
Create Date: 2026-09-08

Context
-------
Supports the scholarship-database quality pass: a dead-link-detection
system needs somewhere to record what it found. Adds four columns to
`scholarships`:

  - application_url: a separate apply link, when different from the
    informational source_url. NULL means "same as source_url."
  - status: a diagnostic string (active/expired/unavailable/needs_review/
    upcoming) distinct from the existing `is_active` boolean. is_active
    stays the one thing matching.py actually filters on -- this migration
    does not touch that query -- status just records WHY a link checker
    made whatever call it made, and is not evaluated elsewhere yet.
  - last_verified_at: when a link checker last confirmed this row.
  - is_recurring_program: whether the opportunity itself (not a single
    winner's payout schedule -- see award_frequency/renewable) runs again
    next year. NULL = not yet determined.

Backfill for existing rows
---------------------------
Every row that existed before this column did was seeded by hand
(source_name IN ('full_seed', 'manual_seed_2')), not verified by any
automated check, so it would be dishonest to default them to `active`.
They're backfilled to `needs_review` -- the same default new rows get --
so nothing claims to be verified until scraper/link_checker.py actually
confirms it. See that script for the pass that then updates each row's
real status.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd9a3f61c8e2b'
down_revision = 'd41f2a9c7b3e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scholarships', sa.Column('application_url', sa.String(length=500), nullable=True))
    op.add_column(
        'scholarships',
        sa.Column('status', sa.String(length=20), nullable=False, server_default='needs_review'),
    )
    op.create_check_constraint(
        'ck_scholarships_status',
        'scholarships',
        "status IN ('active', 'expired', 'unavailable', 'needs_review', 'upcoming')",
    )
    op.add_column('scholarships', sa.Column('last_verified_at', sa.DateTime(), nullable=True))
    op.add_column('scholarships', sa.Column('is_recurring_program', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('scholarships', 'is_recurring_program')
    op.drop_column('scholarships', 'last_verified_at')
    op.drop_constraint('ck_scholarships_status', 'scholarships', type_='check')
    op.drop_column('scholarships', 'status')
    op.drop_column('scholarships', 'application_url')
