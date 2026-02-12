"""add username to users

Revision ID: 20260212_02
Revises: 20260212_01
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa

revision = "20260212_02"
down_revision = "20260212_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=60), nullable=True))
    op.execute(
        """
        WITH base AS (
            SELECT
                id,
                split_part(email, '@', 1) AS local_part,
                row_number() OVER (PARTITION BY split_part(email, '@', 1) ORDER BY created_at, id) AS rn
            FROM users
        )
        UPDATE users u
        SET username = CASE WHEN base.rn = 1 THEN base.local_part ELSE base.local_part || '_' || base.rn::text END
        FROM base
        WHERE u.id = base.id AND u.username IS NULL
        """
    )
    op.alter_column("users", "username", nullable=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "username")
