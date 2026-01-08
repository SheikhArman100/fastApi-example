"""add ai sessions and messages tables

Revision ID: add_ai_tables
Revises: 795b85c8cbcc
Create Date: 2026-01-08 15:09:30.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_ai_tables'
down_revision: str = '795b85c8cbcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ai_sessions table
    op.create_table('ai_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create ai_questions table
    op.create_table('ai_questions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['ai_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create ai_answers table
    op.create_table('ai_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.String(length=36), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['ai_questions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_ai_answers_id'), 'ai_answers', ['id'], unique=False)
    op.create_index(op.f('ix_ai_answers_question_id'), 'ai_answers', ['question_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_ai_answers_question_id'), table_name='ai_answers')
    op.drop_index(op.f('ix_ai_answers_id'), table_name='ai_answers')

    # Drop tables
    op.drop_table('ai_answers')
    op.drop_table('ai_questions')
    op.drop_table('ai_sessions')
