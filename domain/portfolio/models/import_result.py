from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ImportResult:
    """Result of an import operation with detailed metadata."""
    
    success: bool
    import_source: str
    portfolio_id: Optional[str] = None
    portfolio_created: bool = False
    
    # Counts of imported items
    trades_imported: int = 0
    dividends_imported: int = 0
    positions_imported: int = 0
    activity_entries_created: int = 0
    equity_holdings_created: int = 0
    equities_created: int = 0
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error information
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    failed_items: List[Dict[str, Any]] = None
    
    # Warnings and skipped items
    warnings: List[str] = None
    skipped_trades: int = 0
    skipped_dividends: int = 0
    skipped_positions: int = 0
    
    def __post_init__(self):
        """Initialize mutable default values."""
        if self.failed_items is None:
            self.failed_items = []
        if self.warnings is None:
            self.warnings = []
    
    @property
    def total_items_processed(self) -> int:
        """Total number of items that were successfully processed."""
        return (self.trades_imported + self.dividends_imported + 
                self.positions_imported)
    
    @property
    def total_items_skipped(self) -> int:
        """Total number of items that were skipped."""
        return (self.skipped_trades + self.skipped_dividends + 
                self.skipped_positions)
    
    @property
    def total_models_created(self) -> int:
        """Total number of new models created in the database."""
        return (self.activity_entries_created + self.equity_holdings_created + 
                self.equities_created)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Duration of the import in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_failed_item(self, item_type: str, item_data: Dict[str, Any], error: str):
        """Add a failed item with error details."""
        self.failed_items.append({
            'type': item_type,
            'data': item_data,
            'error': error
        })
    
    def mark_failure(self, error_message: str, error_type: str = "ImportError"):
        """Mark the import as failed with error details."""
        self.success = False
        self.error_message = error_message
        self.error_type = error_type
        if not self.completed_at:
            self.completed_at = datetime.now()
    
    def mark_success(self):
        """Mark the import as successful."""
        self.success = True
        if not self.completed_at:
            self.completed_at = datetime.now()
