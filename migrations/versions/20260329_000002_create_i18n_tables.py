"""create i18n tables

Revision ID: 20260329_000002
Revises: 20260328_000001
Create Date: 2026-03-29 13:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260329_000002"
down_revision: Union[str, Sequence[str], None] = "20260328_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_translation_table(table_name: str, value_type: sa.types.TypeEngine) -> None:
    op.create_table(
        table_name,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key1", sa.String(length=128), nullable=False),
        sa.Column("key2", sa.String(length=128), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("values", value_type, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "key1",
            "key2",
            "language_code",
            name=f"uq_{table_name}_key_language",
        ),
    )
    op.create_index(f"ix_{table_name}_key1", table_name, ["key1"], unique=False)
    op.create_index(f"ix_{table_name}_key2", table_name, ["key2"], unique=False)
    op.create_index(
        f"ix_{table_name}_language_code",
        table_name,
        ["language_code"],
        unique=False,
    )


def upgrade() -> None:
    _create_translation_table("translations_small", sa.String(length=256))
    _create_translation_table("translations_medium", sa.String(length=10240))
    _create_translation_table("translations_large", sa.Text())
    _create_translation_table("translations_huge", sa.Text())


def _drop_translation_table(table_name: str) -> None:
    op.drop_index(f"ix_{table_name}_language_code", table_name=table_name)
    op.drop_index(f"ix_{table_name}_key2", table_name=table_name)
    op.drop_index(f"ix_{table_name}_key1", table_name=table_name)
    op.drop_table(table_name)


def downgrade() -> None:
    _drop_translation_table("translations_huge")
    _drop_translation_table("translations_large")
    _drop_translation_table("translations_medium")
    _drop_translation_table("translations_small")
