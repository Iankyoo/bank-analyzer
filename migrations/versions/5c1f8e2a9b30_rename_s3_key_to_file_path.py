"""rename s3_key to file_path

Revision ID: 5c1f8e2a9b30
Revises: a313d60314a7
Create Date: 2026-10-08 22:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c1f8e2a9b30"
down_revision: Union[str, Sequence[str], None] = "a313d60314a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("statements", "s3_key", new_column_name="file_path")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("statements", "file_path", new_column_name="s3_key")
