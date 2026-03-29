"""add i18n lookup indexes

Revision ID: 20260329_000003
Revises: 20260329_000002
Create Date: 2026-03-29 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260329_000003"
down_revision: Union[str, Sequence[str], None] = "20260329_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    table_index_pairs = (
        ("translations_small", "ix_translations_small_lookup"),
        ("translations_medium", "ix_translations_medium_lookup"),
        ("translations_large", "ix_translations_large_lookup"),
        ("translations_huge", "ix_translations_huge_lookup"),
    )
    for table_name, index_name in table_index_pairs:
        if table_name not in existing_tables:
            continue
        existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
        if index_name in existing_indexes:
            continue
        op.create_index(
            index_name,
            table_name,
            ["key1", "key2", "language_code"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    table_index_pairs = (
        ("translations_huge", "ix_translations_huge_lookup"),
        ("translations_large", "ix_translations_large_lookup"),
        ("translations_medium", "ix_translations_medium_lookup"),
        ("translations_small", "ix_translations_small_lookup"),
    )
    for table_name, index_name in table_index_pairs:
        if table_name not in existing_tables:
            continue
        existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
        if index_name not in existing_indexes:
            continue
        op.drop_index(index_name, table_name=table_name)
