"""Domain model for historical equity prices."""

from uuid import UUID
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from core.domain_model import DomainModel

@dataclass
class HistoricalEquityPrice(DomainModel):
    """Represents a historical equity price record."""
    id: UUID
    equity_id: UUID
    price: Decimal
    recorded_at: datetime
