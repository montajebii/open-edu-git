"""Add search_vector column and full-text search setup, plus PDF columns to pamphlet_versions

Revision ID: f82e2db68e42
Revises:
Create Date: 2026-09-03 02:44:45.676934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f82e2db68e42'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add search_vector column to pamphlets
    op.add_column('pamphlets', sa.Column('search_vector', sa.Text(), nullable=True))

    # Create GIN index for full-text search
    op.execute('CREATE INDEX idx_pamphlets_search_vector ON pamphlets USING GIN(search_vector)')

    # Create trigger function to update search_vector
    op.execute("""
        CREATE OR REPLACE FUNCTION update_pamphlet_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector :=
                to_tsvector('persian', COALESCE(NEW.title, '')) ||
                to_tsvector('persian', COALESCE(NEW.grade, '')) ||
                to_tsvector('persian', COALESCE(NEW.subject, '')) ||
                to_tsvector('persian', COALESCE(NEW.chapter, '')) ||
                to_tsvector('persian', COALESCE(NEW.method, '')) ||
                to_tsvector('persian', COALESCE(NEW.difficulty, '')) ||
                to_tsvector('simple', COALESCE(array_to_string(NEW.tags, ' '), ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    op.execute("""
        CREATE TRIGGER trigger_pamphlet_search_vector
        BEFORE INSERT OR UPDATE ON pamphlets
        FOR EACH ROW EXECUTE FUNCTION update_pamphlet_search_vector();
    """)

    # Add PDF columns to pamphlet_versions
    op.add_column('pamphlet_versions', sa.Column('pdf_file_path', sa.Text(), nullable=True))
    op.add_column('pamphlet_versions', sa.Column('pdf_file_type', sa.String(50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop PDF columns from pamphlet_versions
    op.drop_column('pamphlet_versions', 'pdf_file_type')
    op.drop_column('pamphlet_versions', 'pdf_file_path')

    # Drop trigger
    op.execute('DROP TRIGGER IF EXISTS trigger_pamphlet_search_vector ON pamphlets')

    # Drop trigger function
    op.execute('DROP FUNCTION IF EXISTS update_pamphlet_search_vector()')

    # Drop index
    op.execute('DROP INDEX IF EXISTS idx_pamphlets_search_vector')

    # Drop column
    op.drop_column('pamphlets', 'search_vector')