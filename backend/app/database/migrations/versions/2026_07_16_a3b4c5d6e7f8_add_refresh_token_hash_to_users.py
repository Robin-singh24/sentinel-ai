"""add_refresh_token_hash_to_users

Revision ID: a3b4c5d6e7f8
Revises: 7f3a2e1c9b40
Create Date: 2026-07-16 01:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "7f3a2e1c9b40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("refresh_token_hash", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "refresh_token_hash")
