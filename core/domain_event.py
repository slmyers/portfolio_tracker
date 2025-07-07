from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass(kw_only=True)
class DomainEvent:
    """
    Base class for all domain events. Inherit from this class to define specific events.

    Attributes:
        occurred_at (datetime): The time the event occurred.
        metadata (dict): Optional metadata for tracing or correlation.
        version (int): Event version for backward compatibility and event evolution.

    Versioning:
        The `version` field enables event versioning, allowing for backward compatibility and safe evolution of event schemas over time.
        When making breaking changes to event structure, increment the version and handle deserialization accordingly.
    """
    occurred_at: datetime
    # Optionally, you can add a correlation_id or metadata for tracing
    metadata: dict[str, Any] = None
    version: int = 1  # Event versioning for backward compatibility

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
