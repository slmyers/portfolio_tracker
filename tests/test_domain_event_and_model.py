import unittest
from datetime import datetime, timedelta
from core.domain_event import DomainEvent
from core.domain_model import DomainModel

class EventStub(DomainEvent):
    def __init__(self, payload: str, occurred_at: datetime):
        super().__init__(occurred_at=occurred_at)
        self.payload = payload

class DomainModelTestCase(unittest.TestCase):
    def test_record_and_pull_events(self):
        model = DomainModel()
        event1 = EventStub(payload="foo", occurred_at=datetime.utcnow())
        event2 = EventStub(payload="bar", occurred_at=datetime.utcnow() + timedelta(seconds=1))
        model.record_event(event1)
        model.record_event(event2)
        events = model.pull_events()
        self.assertEqual(events, [event1, event2])
        # After pulling, events should be cleared
        self.assertEqual(model.pull_events(), [])

    def test_domain_event_metadata(self):
        event = DomainEvent(occurred_at=datetime.utcnow())
        self.assertIsInstance(event.metadata, dict)
        self.assertEqual(event.metadata, {})
        # Can add metadata
        event.metadata['key'] = 'value'
        self.assertEqual(event.metadata['key'], 'value')
