"""Install pamphlet full-text-search trigger

Revision ID: f82e2db68e42
Revises: 470ddd355943
Create Date: 2026-09-03 02:44:45.676934

This revision originally tried to add the ``pamphlets.search_vector``
column itself (as ``sa.Text()`` — invalid for tsvector data and for the GIN
index it created) and assumed the base tables already existed, which they
never did. The baseline revision 470ddd355943 now creates the tables, the
native TSVECTOR column and the GIN index; this revision only installs the
Persian full-text-search trigger that keeps the column populated. The tags
JSON column is indexed via ``tags::text`` (``array_to_string`` does not
accept ``json`` input).
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f82e2db68e42"
down_revision: str | Sequence[str] | None = "470ddd355943"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Install the trigger function and trigger."""
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
                to_tsvector('simple', COALESCE(NEW.tags::text, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_pamphlet_search_vector
        BEFORE INSERT OR UPDATE ON pamphlets
        FOR EACH ROW EXECUTE FUNCTION update_pamphlet_search_vector();
    """)


def downgrade() -> None:
    """Remove the trigger and its function."""
    op.execute("DROP TRIGGER IF EXISTS trigger_pamphlet_search_vector ON pamphlets")
    op.execute("DROP FUNCTION IF EXISTS update_pamphlet_search_vector()")
