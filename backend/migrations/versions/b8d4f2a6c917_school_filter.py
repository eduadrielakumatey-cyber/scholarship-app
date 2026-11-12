"""school filter: scholarships tied to one college, and the colleges a student picked

Revision ID: b8d4f2a6c917
Revises: a7c3e9f1d248
Create Date: 2026-11-11

scholarships.school -- the one college a winner must attend (NULL = any).
users.schools       -- colleges the student attends or is considering
                       (NULL = not answered, so nothing is hidden).

Every listing pulled from a college's own AcademicWorks portal is that
college's award, so those rows are backfilled with their organization.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = 'b8d4f2a6c917'
down_revision = 'a7c3e9f1d248'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scholarships', sa.Column('school', sa.String(length=160), nullable=True))
    op.add_column('users', sa.Column('schools', ARRAY(sa.String()), nullable=True))
    op.execute(
        "UPDATE scholarships SET school = organization "
        "WHERE source_url LIKE 'https://%.academicworks.com/%' AND organization IS NOT NULL"
    )


def downgrade():
    op.drop_column('users', 'schools')
    op.drop_column('scholarships', 'school')
