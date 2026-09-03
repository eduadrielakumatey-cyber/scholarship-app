"""award structure fields, majors_are_hard_requirement, and interactions
drift reconciliation

Revision ID: b986668e3686
Revises: fca209c659ba
Create Date: 2026-09-01

Context
-------
This migration supports the new 4-layer recommendation architecture
(Hard Eligibility / Match Quality / Application Value / User Preferences).

Two things it does, deliberately conservative:

1. Renames `scholarships.amount` -> `scholarships.award_amount` using a
   native ALTER TABLE ... RENAME COLUMN, which preserves every existing
   value in place (this is NOT drop-then-add -- verified against the dev
   database before this migration was considered done; see the
   implementation report for the row-count/value-preservation check).

2. Adds `award_frequency` (one_time | annual | unknown), `renewable`,
   and `renewal_years`. Per explicit product direction: a lack of
   evidence about a scholarship's award structure is NOT the same as
   verified evidence that it's a one-time award, so every existing row
   defaults to `award_frequency = 'unknown'`, `renewable = NULL`,
   `renewal_years = NULL`. Nothing is inferred here. A small, separate,
   already-reviewed script (backfill_award_structure.py) fills in the
   handful of records where the real structure was independently
   verified via research, and is run AFTER this migration, not as part
   of it -- this migration only builds the shape, it doesn't guess data.

3. Adds `majors_are_hard_requirement` (default false) so eligibility can
   distinguish "legally/structurally major-restricted" from "major listed
   as a soft preference," per the Hard Eligibility layer redesign.

It also reconciles a pre-existing drift discovered while writing this
migration: `interactions.app_status` exists in the live database (added
by a one-off script, migrate_status.py, run outside Alembic) but was
never captured in migration history, so a *fresh* install from scratch
would be missing it. The idempotent `ADD COLUMN IF NOT EXISTS` below
fixes that going forward without touching any database that already has
the column (this one included).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b986668e3686'
down_revision = 'fca209c659ba'
branch_labels = None
depends_on = None


def upgrade():
    # --- 1. amount -> award_amount (in-place rename, preserves data) ---
    op.alter_column(
        'scholarships', 'amount',
        new_column_name='award_amount',
        existing_type=sa.Numeric(precision=10, scale=2),
        existing_nullable=False,
    )

    # --- 2. New award-structure fields, all default to "we don't know" ---
    op.add_column(
        'scholarships',
        sa.Column('award_frequency', sa.String(length=10), nullable=False, server_default='unknown'),
    )
    op.create_check_constraint(
        'ck_scholarships_award_frequency',
        'scholarships',
        "award_frequency IN ('one_time', 'annual', 'unknown')",
    )
    op.add_column('scholarships', sa.Column('renewable', sa.Boolean(), nullable=True))
    op.add_column('scholarships', sa.Column('renewal_years', sa.Integer(), nullable=True))

    # --- 3. Eligibility-layer field ---
    op.add_column(
        'scholarships',
        sa.Column('majors_are_hard_requirement', sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # --- 4. Reconcile pre-existing interactions.app_status drift (idempotent) ---
    op.execute(
        "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS app_status VARCHAR(20) DEFAULT 'saved'"
    )


def downgrade():
    op.drop_column('scholarships', 'majors_are_hard_requirement')
    op.drop_column('scholarships', 'renewal_years')
    op.drop_column('scholarships', 'renewable')
    op.drop_constraint('ck_scholarships_award_frequency', 'scholarships', type_='check')
    op.drop_column('scholarships', 'award_frequency')
    op.alter_column(
        'scholarships', 'award_amount',
        new_column_name='amount',
        existing_type=sa.Numeric(precision=10, scale=2),
        existing_nullable=False,
    )
    # app_status is intentionally left in place on downgrade -- it predates
    # this migration and other code depends on it existing.
