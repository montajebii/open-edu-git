"""Add IP% and credential fields to pamphlets and users

Revision ID: 46e78ee4439d
Revises: f82e2db68e42
Create Date: 2026-09-03 03:21:52.428712

The columns are already part of the baseline revision 470ddd355943, so on
databases migrated from empty this revision is a no-op. The existence guards
keep it correct for databases bootstrapped from the legacy init.sql, where
these columns were genuinely missing.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect as sa_inspect

# revision identifiers, used by Alembic.
revision: str = "46e78ee4439d"
down_revision: str | Sequence[str] | None = "f82e2db68e42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_CREDENTIAL_COLUMNS = [
    (
        "pamphlet_count",
        lambda: sa.Column("pamphlet_count", sa.Integer(), nullable=True, server_default="0"),
    ),
    (
        "total_downloads",
        lambda: sa.Column("total_downloads", sa.Integer(), nullable=True, server_default="0"),
    ),
    (
        "average_rating",
        lambda: sa.Column("average_rating", sa.Float(), nullable=True, server_default="0.0"),
    ),
    (
        "total_reviews",
        lambda: sa.Column("total_reviews", sa.Integer(), nullable=True, server_default="0"),
    ),
    (
        "forks_received",
        lambda: sa.Column("forks_received", sa.Integer(), nullable=True, server_default="0"),
    ),
    (
        "merges_approved",
        lambda: sa.Column("merges_approved", sa.Integer(), nullable=True, server_default="0"),
    ),
    (
        "credential_score",
        lambda: sa.Column("credential_score", sa.Float(), nullable=True, server_default="0.0"),
    ),
]


def _column_names(bind, table: str) -> set[str]:
    return {col["name"] for col in sa_inspect(bind).get_columns(table)}


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    if "original_author_ip_percentage" not in _column_names(bind, "pamphlets"):
        op.add_column(
            "pamphlets",
            sa.Column(
                "original_author_ip_percentage", sa.Float(), nullable=True, server_default="100.0"
            ),
        )

    existing = _column_names(bind, "users")
    for name, column in USER_CREDENTIAL_COLUMNS:
        if name not in existing:
            op.add_column("users", column())


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    existing = _column_names(bind, "users")
    for name, _column in reversed(USER_CREDENTIAL_COLUMNS):
        if name in existing:
            op.drop_column("users", name)

    if "original_author_ip_percentage" in _column_names(bind, "pamphlets"):
        op.drop_column("pamphlets", "original_author_ip_percentage")
