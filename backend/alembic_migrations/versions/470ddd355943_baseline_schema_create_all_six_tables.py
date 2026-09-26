"""Baseline schema: create all six tables with PostgreSQL-native types

Revision ID: 470ddd355943
Revises:
Create Date: 2026-09-27

Baseline migration generated from ``app.db.models`` (the canonical schema).
It replaces the stale ``backend/migrations/init.sql`` bootstrap, which
created integer PKs and predated the forks/merge_requests tables and the
pamphlet_versions file-metadata columns.

NOTE: revision f82e2db68e42 (search_vector) assumed this baseline already
existed but never created the underlying tables, so a fresh database could
never be migrated from empty. That revision was rewritten to only install
the full-text-search trigger; the tsvector column and GIN index are created
here as first-class PostgreSQL types instead of the broken ``sa.Text()``
column it used to add (tsvector data in a text column, which also made the
GIN index invalid).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "470ddd355943"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MERGE_REQUEST_STATUS = sa.Enum("pending", "approved", "rejected", name="mergerequeststatus")


def upgrade() -> None:
    """Create the full baseline schema."""

    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # PostgreSQL ships no built-in 'persian' text-search configuration, yet the
    # application queries `plainto_tsquery('persian', ...)` and the FTS trigger
    # calls `to_tsvector('persian', ...)`. Create one copied from 'simple'
    # (token-level matching, no stemming) so both work on any fresh database.
    op.execute("""
        DO $txs$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'persian') THEN
                CREATE TEXT SEARCH CONFIGURATION persian (COPY = simple);
            END IF;
        END
        $txs$;
    """)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=50), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("expertise_tags", sa.JSON(), nullable=True),
        sa.Column("pamphlet_count", sa.Integer(), nullable=True),
        sa.Column("total_downloads", sa.Integer(), nullable=True),
        sa.Column("average_rating", sa.Float(), nullable=True),
        sa.Column("total_reviews", sa.Integer(), nullable=True),
        sa.Column("forks_received", sa.Integer(), nullable=True),
        sa.Column("merges_approved", sa.Integer(), nullable=True),
        sa.Column("credential_score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "pamphlets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("grade", sa.String(length=50), nullable=False),
        sa.Column("subject", sa.String(length=100), nullable=False),
        sa.Column("chapter", sa.String(length=100), nullable=False),
        sa.Column("method", sa.String(length=100), nullable=True),
        sa.Column("difficulty", sa.String(length=50), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("original_author_ip_percentage", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_pamphlets_search_vector",
        "pamphlets",
        ["search_vector"],
        postgresql_using="gin",
    )

    op.create_table(
        "pamphlet_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pamphlet_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("pdf_file_path", sa.String(length=512), nullable=True),
        sa.Column("pdf_file_type", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["pamphlet_id"], ["pamphlets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pamphlet_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["pamphlet_id"], ["pamphlets.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "forks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("original_pamphlet_id", sa.Uuid(), nullable=False),
        sa.Column("forked_by", sa.Uuid(), nullable=False),
        sa.Column("new_pamphlet_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["forked_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["new_pamphlet_id"], ["pamphlets.id"]),
        sa.ForeignKeyConstraint(["original_pamphlet_id"], ["pamphlets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "merge_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_pamphlet_id", sa.Uuid(), nullable=False),
        sa.Column("target_pamphlet_id", sa.Uuid(), nullable=False),
        sa.Column("status", MERGE_REQUEST_STATUS, nullable=False, server_default="pending"),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_pamphlet_id"], ["pamphlets.id"]),
        sa.ForeignKeyConstraint(["target_pamphlet_id"], ["pamphlets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop the baseline schema."""
    op.drop_table("merge_requests")
    op.drop_table("forks")
    op.drop_table("reviews")
    op.drop_table("pamphlet_versions")
    op.drop_index("ix_pamphlets_search_vector", table_name="pamphlets")
    op.drop_table("pamphlets")
    op.drop_table("users")
    op.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS persian")
    MERGE_REQUEST_STATUS.drop(op.get_bind(), checkfirst=True)
