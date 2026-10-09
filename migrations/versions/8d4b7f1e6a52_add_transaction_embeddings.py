"""add transaction_embeddings with pgvector

Revision ID: 8d4b7f1e6a52
Revises: 5c1f8e2a9b30
Create Date: 2026-10-08 23:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8d4b7f1e6a52"
down_revision: Union[str, Sequence[str], None] = "5c1f8e2a9b30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "transaction_embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column(
            "category",
            # o tipo "category" já existe, criado junto com a tabela transactions
            postgresql.ENUM(name="category", create_type=False),
            nullable=False,
        ),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_transaction_embeddings_user_id", "transaction_embeddings", ["user_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_transaction_embeddings_user_id", table_name="transaction_embeddings"
    )
    op.drop_table("transaction_embeddings")
    op.execute("DROP EXTENSION IF EXISTS vector")
