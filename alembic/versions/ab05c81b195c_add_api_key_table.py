"""Add API key table

Revision ID: ab05c81b195c
Revises: df86402e5db2
Create Date: 2026-07-07 18:22:30.827556
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "ab05c81b195c"
down_revision: Union[str, Sequence[str], None] = "df86402e5db2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "api_keys",
        sa.Column("api_key_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("secret_digest", sa.String(length=64), nullable=False),
        sa.Column(
            "hmac_key_version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "char_length(name) BETWEEN 1 AND 100",
            name="ck_api_keys_name_length_valid",
        ),
        sa.CheckConstraint(
            "char_length(secret_digest) = 64",
            name="ck_api_keys_secret_digest_length",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_api_keys_expires_after_creation",
        ),
        sa.CheckConstraint(
            "hmac_key_version > 0",
            name="ck_api_keys_hmac_key_version_positive",
        ),
        sa.CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= created_at",
            name="ck_api_keys_revoked_not_before_creation",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.tenant_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("api_key_id"),
    )

    op.create_index(
        op.f("ix_api_keys_tenant_id"),
        "api_keys",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_api_keys_tenant_id"),
        table_name="api_keys",
    )
    op.drop_table("api_keys")
