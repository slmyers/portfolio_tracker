"""create-historical-equity-table

Revision ID: f5f03e6bdbf7
Revises: b2c4fa7a944a
Create Date: 2025-07-12 13:17:03.646952

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f5f03e6bdbf7'
down_revision: Union[str, Sequence[str], None] = 'b2c4fa7a944a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create historical_equity_price table with composite primary key
    op.execute(
        """
        CREATE TABLE historical_equity_price (
            id UUID NOT NULL,
            equity_id UUID NOT NULL,
            price DECIMAL NOT NULL,
            recorded_at TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (id, recorded_at, equity_id)
        );
        """
    )

    # Convert the table to a hypertable partitioned on recorded_at and equity_id with 4 space partitions
    op.execute(
        """
        SELECT create_hypertable('historical_equity_price', 'recorded_at', 'equity_id', 4);
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the historical_equity_price table
    op.execute(
        """
        DROP TABLE historical_equity_price;
        """
    )
