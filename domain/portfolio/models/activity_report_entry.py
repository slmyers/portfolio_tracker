from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from core.domain_model import DomainModel
from .enums import Currency


class ActivityReportEntry(DomainModel):
    """Entity representing an activity report entry in a portfolio."""
    
    def __init__(
        self,
        id: UUID,
        portfolio_id: UUID,
        equity_id: Optional[UUID],
        activity_type: str,
        amount: Decimal,
        currency: Currency,
        date: datetime,
        raw_data: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ):
        super().__init__()
        self.id = id
        self.portfolio_id = portfolio_id
        self.equity_id = equity_id
        self.activity_type = activity_type
        self.amount = amount
        self.currency = currency
        self.date = date
        self.raw_data = raw_data or {}
        self.created_at = created_at or datetime.utcnow()

    @property
    def stock_id(self) -> Optional[UUID]:
        """Alias for equity_id for backward compatibility."""
        return self.equity_id