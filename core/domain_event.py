from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class DomainEvent:
    """
    Base class for all domain events. Inherit from this class to define specific events.
    """
    occurred_at: datetime
    # Optionally, you can add a correlation_id or metadata for tracing
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
