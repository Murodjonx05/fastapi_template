"""create rbac tables

Revision ID: 20260329_000004
Revises: 20260329_000003
Create Date: 2026-03-29 14:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260329_000004"
down_revision: Union[str, Sequence[str], None] = "20260329_000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("title_key1", sa.String(length=128), nullable=False),
        sa.Column("title_key2", sa.String(length=128), nullable=False),
        sa.Column("description_key1", sa.String(length=128), nullable=False),
        sa.Column("description_key2", sa.String(length=128), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("title_key1", sa.String(length=128), nullable=False),
        sa.Column("title_key2", sa.String(length=128), nullable=False),
        sa.Column("description_key1", sa.String(length=128), nullable=False),
        sa.Column("description_key2", sa.String(length=128), nullable=False),
        sa.Column("permissions_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permissions_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "plugin_permissions",
        sa.Column("permissions_id", sa.Integer(), nullable=False),
        sa.Column("plugin_name", sa.String(length=255), nullable=False),
        sa.Column("access_key_hash", sa.String(length=64), nullable=False),
        sa.Column("permissions_dict", sa.JSON(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permissions_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "permissions_id",
            "plugin_name",
            name="uq_plugin_permissions_container_plugin",
        ),
        sa.UniqueConstraint(
            "access_key_hash",
            name="uq_plugin_permissions_access_key_hash",
        ),
    )


def downgrade() -> None:
    op.drop_table("plugin_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
