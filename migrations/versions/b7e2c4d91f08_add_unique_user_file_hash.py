"""add unique constraint on statements (user_id, file_hash)

Revision ID: b7e2c4d91f08
Revises: 8d4b7f1e6a52
Create Date: 2026-10-09 00:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7e2c4d91f08"
down_revision: Union[str, Sequence[str], None] = "8d4b7f1e6a52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_statements_user_file_hash", "statements", ["user_id", "file_hash"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_statements_user_file_hash", "statements", type_="unique")
