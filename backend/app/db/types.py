"""
Custom SQLAlchemy types for OpenEdu Git.
"""

import sqlalchemy as sa


class TSVector(sa.types.UserDefinedType):
    """Cross-dialect ``tsvector`` column type.

    Renders as PostgreSQL ``TSVECTOR`` (enabling the GIN full-text index and
    trigger-maintained lexical search) and falls back to plain ``TEXT`` on
    every other dialect so the SQLite-based test suite can create the tables.
    """

    cache_ok = True

    def get_col_spec(self, **kw):  # noqa: ARG002 - signature fixed by SQLAlchemy
        return "TSVECTOR"

    def bind_processor(self, dialect):
        if dialect.name == "postgresql":
            return None  # server-side trigger owns the value

        def process(value):
            return value

        return process

    def result_processor(self, dialect, coltype):  # noqa: ARG002 - signature fixed by SQLAlchemy
        if dialect.name == "postgresql":
            return None  # return the raw tsvector string representation

        def process(value):
            return value

        return process
