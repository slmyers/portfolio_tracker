from typing import List
from .domain_event import DomainEvent

class DomainModel:
    """
    Base class for all aggregate roots and entities in the domain.
    Provides domain event recording and retrieval.
    """
    def __init__(self):
        self._events: List[DomainEvent] = []

    def record_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> List[DomainEvent]:
        events = self._events[:]
        self._events.clear()
        return events
