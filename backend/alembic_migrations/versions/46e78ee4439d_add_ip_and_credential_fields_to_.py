"""Add IP% and credential fields to pamphlets and users

Revision ID: 46e78ee4439d
Revises: f82e2db68e42
Create Date: 2026-09-03 03:21:52.428712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46e78ee4439d'
down_revision: Union[str, Sequence[str], None] = 'f82e2db68e42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add IP% column to pamphlets
    op.add_column('pamphlets', sa.Column('original_author_ip_percentage', sa.Float(), nullable=True, server_default='100.0'))

    # Add credential columns to users
    op.add_column('users', sa.Column('pamphlet_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('total_downloads', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('average_rating', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('users', sa.Column('total_reviews', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('forks_received', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('merges_approved', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('credential_score', sa.Float(), nullable=True, server_default='0.0'))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop credential columns from users
    op.drop_column('users', 'credential_score')
    op.drop_column('users', 'merges_approved')
    op.drop_column('users', 'forks_received')
    op.drop_column('users', 'total_reviews')
    op.drop_column('users', 'average_rating')
    op.drop_column('users', 'total_downloads')
    op.drop_column('users', 'pamphlet_count')

    # Drop IP% column from pamphlets
    op.drop_column('pamphlets', 'original_author_ip_percentage')