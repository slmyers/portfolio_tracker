from uuid import UUID
from datetime import datetime
from core.domain_model import DomainModel
from typing import Optional

class Stock(DomainModel):
    """Stock entity representing a stock/security in the system."""
    
    def __init__(
        self,
        id: UUID,
        symbol: str,
        name: Optional[str] = None,
        exchange: Optional[str] = None,
        currency: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__()
        self.id = id
        self.symbol = symbol
        self.name = name
        self.exchange = exchange
        self.currency = currency
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at

    def update_info(self, name: Optional[str] = None, exchange: Optional[str] = None, currency: Optional[str] = None):
        """Update stock information."""
        if name is not None:
            self.name = name
        if exchange is not None:
            self.exchange = exchange
        if currency is not None:
            self.currency = currency
        self.updated_at = datetime.utcnow()
