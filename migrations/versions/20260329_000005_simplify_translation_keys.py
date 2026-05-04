"""simplify translation and rbac key columns

Revision ID: 20260329_000005
Revises: 20260329_000004
Create Date: 2026-03-29 16:10:00

WARNING — SQLite safety note
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This migration uses ``batch_alter_table(recreate="always")`` which copies
the entire table into a temporary table and recreates it.  This is the
only reliable way to rename / drop columns on SQLite, but it can be
**very slow and memory-intensive** on large tables because every row is
copied.  On PostgreSQL / MySQL the same operations are near-instant
in-place DDL.

If you are running against a production SQLite database with millions of
rows, consider:
  1. Scheduling a maintenance window.
  2. Taking a backup before applying this migration.
  3. Migrating to PostgreSQL for large-scale deployments.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.utils.logging import get_logger

_log = get_logger("migration_000005")

# revision identifiers, used by Alembic.
revision: str = "20260329_000005"
down_revision: Union[str, Sequence[str], None] = "20260329_000004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

I18N_TABLES = (
    "translations_small",
    "translations_medium",
    "translations_large",
    "translations_huge",
)

# Row-count threshold above which a warning is emitted before the costly
# ``recreate="always"`` operation.  Adjust as needed.
_LARGE_TABLE_THRESHOLD = 100_000


def _warn_if_large(bind: sa.engine.Connection, table_name: str) -> None:
    """Log a warning when a table exceeds *_LARGE_TABLE_THRESHOLD* rows.

    This does NOT block the migration — it only makes the operator aware
    that the recreate step may take a significant amount of time.
    """
    row_count = bind.execute(
        sa.text(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
    ).scalar()
    if row_count and row_count > _LARGE_TABLE_THRESHOLD:
        _log.warning(
            f"Table '{table_name}' has {row_count:,} rows.  "
            f"The recreate='always' step may be slow on SQLite.  "
            f"Consider backing up the database before proceeding.",
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table_name in I18N_TABLES:
        indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
        for index_name in (
            f"ix_{table_name}_lookup",
            f"ix_{table_name}_key1",
            f"ix_{table_name}_key2",
        ):
            if index_name in indexes:
                op.drop_index(index_name, table_name=table_name)

        unique_names = {u["name"] for u in inspector.get_unique_constraints(table_name)}
        uq_name = f"uq_{table_name}_key_language"
        _warn_if_large(bind, table_name)
        with op.batch_alter_table(
            table_name,
            recreate="always",
            partial_reordering=("id", "key", "language_code", "values"),
        ) as batch_op:
            if uq_name in unique_names:
                batch_op.drop_constraint(uq_name, type_="unique")
            batch_op.alter_column("key1", new_column_name="key")
            batch_op.drop_column("key2")
            batch_op.create_unique_constraint(
                uq_name,
                ["key", "language_code"],
            )

        op.create_index(f"ix_{table_name}_key", table_name, ["key"], unique=False)
        op.create_index(
            f"ix_{table_name}_lookup",
            table_name,
            ["key", "language_code"],
            unique=False,
        )

    for table_name in ("permissions", "rbac"):
        desired_order = (
            ("id", "name", "title_key", "description_key")
            if table_name == "permissions"
            else ("id", "name", "title_key", "description_key", "permissions_id")
        )
        _warn_if_large(bind, table_name)
        with op.batch_alter_table(
            table_name,
            recreate="always",
            partial_reordering=desired_order,
        ) as batch_op:
            batch_op.alter_column("title_key1", new_column_name="title_key")
            batch_op.drop_column("title_key2")
            batch_op.alter_column("description_key1", new_column_name="description_key")
            batch_op.drop_column("description_key2")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table_name in ("permissions", "rbac"):
        desired_order = (
            ("id", "name", "title_key1", "title_key2", "description_key1", "description_key2")
            if table_name == "permissions"
            else (
                "id",
                "name",
                "title_key1",
                "title_key2",
                "description_key1",
                "description_key2",
                "permissions_id",
            )
        )
        with op.batch_alter_table(
            table_name,
            recreate="always",
            partial_reordering=desired_order,
        ) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "title_key2",
                    sa.String(length=128),
                    nullable=False,
                    server_default="",
                )
            )
            batch_op.add_column(
                sa.Column(
                    "description_key2",
                    sa.String(length=128),
                    nullable=False,
                    server_default="",
                )
            )
            batch_op.alter_column("title_key", new_column_name="title_key1")
            batch_op.alter_column("description_key", new_column_name="description_key1")

    for table_name in I18N_TABLES:
        indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
        for index_name in (f"ix_{table_name}_lookup", f"ix_{table_name}_key"):
            if index_name in indexes:
                op.drop_index(index_name, table_name=table_name)

        unique_names = {u["name"] for u in inspector.get_unique_constraints(table_name)}
        uq_name = f"uq_{table_name}_key_language"
        with op.batch_alter_table(
            table_name,
            recreate="always",
            partial_reordering=("id", "key1", "key2", "language_code", "values"),
        ) as batch_op:
            if uq_name in unique_names:
                batch_op.drop_constraint(uq_name, type_="unique")
            batch_op.add_column(
                sa.Column(
                    "key2",
                    sa.String(length=128),
                    nullable=False,
                    server_default="",
                )
            )
            batch_op.alter_column("key", new_column_name="key1")
            batch_op.create_unique_constraint(
                uq_name,
                ["key1", "key2", "language_code"],
            )
        op.create_index(f"ix_{table_name}_key1", table_name, ["key1"], unique=False)
        op.create_index(f"ix_{table_name}_key2", table_name, ["key2"], unique=False)
        op.create_index(
            f"ix_{table_name}_lookup",
            table_name,
            ["key1", "key2", "language_code"],
            unique=False,
        )
