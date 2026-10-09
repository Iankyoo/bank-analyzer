"""add ai_insight to statements

Revision ID: c3a9e5f27d14
Revises: b7e2c4d91f08
Create Date: 2026-10-09 01:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3a9e5f27d14"
down_revision: Union[str, Sequence[str], None] = "b7e2c4d91f08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("statements", sa.Column("ai_insight", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("statements", "ai_insight")
