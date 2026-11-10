"""application questions on scholarships, and students' saved answers

Revision ID: f5b2d8e4a613
Revises: e3a9c5d7f210
Create Date: 2026-11-10
"""
from alembic import op
import sqlalchemy as sa

revision = 'f5b2d8e4a613'
down_revision = 'e3a9c5d7f210'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scholarships', sa.Column('questions', sa.JSON(), nullable=True))
    op.create_table(
        'answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scholarship_id', sa.Integer(), sa.ForeignKey('scholarships.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_key', sa.String(16), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'scholarship_id', 'question_key', name='uq_answer_user_question'),
    )
    op.create_index('ix_answers_user_id', 'answers', ['user_id'])
    op.create_index('ix_answers_scholarship_id', 'answers', ['scholarship_id'])


def downgrade():
    op.drop_index('ix_answers_scholarship_id', table_name='answers')
    op.drop_index('ix_answers_user_id', table_name='answers')
    op.drop_table('answers')
    op.drop_column('scholarships', 'questions')
