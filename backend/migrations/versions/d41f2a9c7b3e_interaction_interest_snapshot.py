"""interactions.interest_snapshot for recommendation refresh

Revision ID: d41f2a9c7b3e
Revises: b986668e3686
Create Date: 2026-09-07

Context
-------
Supports the "recommendations should reflect the user's CURRENT profile,
not be permanently frozen by old swipes" fix in
app/services/matching.py:get_swipe_deck.

Previously, once a user passed on a scholarship it was excluded from
their deck forever, even if they later added an interest that made it a
strong match. This adds `interactions.interest_snapshot`: the user's
normalized interests at the moment of the interaction. It's only
consulted for `action = 'pass'` rows -- matching.py compares it against
the user's current interests to decide whether a skip is stale enough to
reconsider. See matching.py:_reentry_ids for the comparison rule.

Existing rows get NULL, treated by that comparison as "unknown baseline"
(i.e. any current interest counts as new) rather than backfilled with a
guess -- there's no historical record of what a user's interests were
when they passed on something before this column existed.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd41f2a9c7b3e'
down_revision = 'b986668e3686'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'interactions',
        sa.Column('interest_snapshot', postgresql.ARRAY(sa.String()), nullable=True),
    )


def downgrade():
    op.drop_column('interactions', 'interest_snapshot')
