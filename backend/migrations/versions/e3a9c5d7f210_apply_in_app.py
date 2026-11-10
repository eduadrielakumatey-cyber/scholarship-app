"""apply in app: essay library, sponsor-posted scholarships, in-app applications

Revision ID: e3a9c5d7f210
Revises: c7e1a4d8b952
Create Date: 2026-11-09
"""
from alembic import op
import sqlalchemy as sa

revision = 'e3a9c5d7f210'
down_revision = 'c7e1a4d8b952'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scholarships', sa.Column('hosted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('scholarships', sa.Column('essay_prompt', sa.Text(), nullable=True))
    op.add_column('scholarships', sa.Column('sponsor_name', sa.String(160), nullable=True))
    op.add_column('scholarships', sa.Column('sponsor_email', sa.String(255), nullable=True))
    op.add_column('scholarships', sa.Column('review_token_hash', sa.String(64), nullable=True))
    op.create_unique_constraint('uq_scholarships_review_token_hash', 'scholarships', ['review_token_hash'])

    op.create_table(
        'essays',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(160), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_essays_user_id', 'essays', ['user_id'])

    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('scholarship_id', sa.Integer(), sa.ForeignKey('scholarships.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('full_name', sa.String(120), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('school', sa.String(160), nullable=True),
        sa.Column('essay', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='submitted'),
        sa.Column('consented_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('scholarship_id', 'user_id', name='uq_application_user_scholarship'),
    )
    op.create_index('ix_applications_scholarship_id', 'applications', ['scholarship_id'])
    op.create_index('ix_applications_user_id', 'applications', ['user_id'])


def downgrade():
    op.drop_index('ix_applications_user_id', table_name='applications')
    op.drop_index('ix_applications_scholarship_id', table_name='applications')
    op.drop_table('applications')
    op.drop_index('ix_essays_user_id', table_name='essays')
    op.drop_table('essays')
    op.drop_constraint('uq_scholarships_review_token_hash', 'scholarships', type_='unique')
    for col in ('review_token_hash', 'sponsor_email', 'sponsor_name', 'essay_prompt', 'hosted'):
        op.drop_column('scholarships', col)
