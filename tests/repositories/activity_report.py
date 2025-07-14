"""Test-specific in-memory activity report entry repository with mocking and assertion utilities."""

from typing import Optional, List, Dict
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime

from domain.portfolio.models.activity_report_entry import ActivityReportEntry


class TestActivityReportEntryRepository:
    """Test-specific in-memory implementation of ActivityReportEntryRepository with utilities for testing."""
    
    def __init__(self):
        self._entries: Dict[UUID, dict] = {}
        self._call_history: List[dict] = []

    def find_by_portfolio_id(
        self, 
        portfolio_id: UUID, 
        *, 
        limit: int = 100, 
        offset: int = 0, 
        activity_type: Optional[str] = None, 
        conn=None
    ) -> List[ActivityReportEntry]:
        self._record_call('find_by_portfolio_id', {
            'portfolio_id': portfolio_id, 
            'limit': limit, 
            'offset': offset,
            'activity_type': activity_type
        })
        entries = [
            self._row_to_entry(row) 
            for row in self._entries.values() 
            if row['portfolio_id'] == portfolio_id and (
                activity_type is None or row['activity_type'] == activity_type
            )
        ]
        return entries[offset:offset + limit]

    def get(self, entry_id: UUID, conn=None) -> Optional[ActivityReportEntry]:
        self._record_call('get', {'entry_id': entry_id})
        row = self._entries.get(entry_id)
        return self._row_to_entry(row) if row else None

    def find_by_date_range(
        self, 
        portfolio_id: UUID, 
        start_date: str, 
        end_date: str, 
        conn=None
    ) -> List[ActivityReportEntry]:
        self._record_call('find_by_date_range', {
            'portfolio_id': portfolio_id, 
            'start_date': start_date,
            'end_date': end_date
        })
        return [
            self._row_to_entry(row) 
            for row in self._entries.values() 
            if (row['portfolio_id'] == portfolio_id and 
                start_date <= row['date'] <= end_date)
        ]

    def save(self, entry: ActivityReportEntry, conn=None) -> None:
        self._record_call('save', {'entry_id': entry.id})
        self._entries[entry.id] = self._entry_to_row(entry)

    def delete(self, entry_id: UUID, conn=None) -> None:
        self._record_call('delete', {'entry_id': entry_id})
        self._entries.pop(entry_id, None)

    def batch_save(self, entries: List[ActivityReportEntry], conn=None) -> None:
        self._record_call('batch_save', {'count': len(entries)})
        for entry in entries:
            self.save(entry, conn)

    def exists(self, entry_id: UUID, conn=None) -> bool:
        self._record_call('exists', {'entry_id': entry_id})
        return entry_id in self._entries

    def _entry_to_row(self, entry: ActivityReportEntry) -> dict:
        return {
            'id': entry.id,
            'portfolio_id': entry.portfolio_id,
            'equity_id': entry.equity_id,
            'currency': entry.currency,
            'activity_type': entry.activity_type,
            'amount': entry.amount,
            'date': entry.date,
            'raw_data': entry.raw_data,
            'created_at': entry.created_at,
        }

    def _row_to_entry(self, row: dict) -> ActivityReportEntry:
        """Create an ActivityReportEntry object without triggering events."""
        entry = ActivityReportEntry.__new__(ActivityReportEntry)
        entry._events = []  # Initialize the events list
        entry.id = row['id']
        entry.portfolio_id = row['portfolio_id']
        entry.equity_id = row['equity_id']
        entry.currency = row['currency']
        entry.activity_type = row['activity_type']
        entry.amount = row['amount']
        entry.date = row['date']
        entry.raw_data = row['raw_data']
        entry.created_at = row['created_at']
        return entry

    def _record_call(self, method: str, args: dict):
        """Record method calls for testing assertions."""
        self._call_history.append({
            'method': method,
            'args': args,
            'timestamp': datetime.now()
        })

    # Test utility methods
    def mock_activity_report_entry(
        self, 
        entry_id: UUID = None,
        portfolio_id: UUID = None,
        equity_id: UUID = None,
        currency = None,
        activity_type: str = "BUY",
        amount: Decimal = Decimal('100.00'),
        date: str = None,
        raw_data: dict = None,
        created_at: datetime = None
    ) -> ActivityReportEntry:
        """Create and save a mock activity report entry for testing."""
        from domain.portfolio.models.enums import Currency
        
        entry_id = entry_id or uuid4()
        portfolio_id = portfolio_id or uuid4()
        equity_id = equity_id or uuid4()
        currency = currency or Currency.USD
        date = date or datetime.now().strftime('%Y-%m-%d')
        raw_data = raw_data or {}
        created_at = created_at or datetime.now()
        
        entry = ActivityReportEntry(
            id=entry_id,
            portfolio_id=portfolio_id,
            equity_id=equity_id,
            currency=currency,
            activity_type=activity_type,
            amount=amount,
            date=date,
            raw_data=raw_data
        )
        entry.created_at = created_at
        
        self.save(entry)
        return entry

    def assert_entry_exists(self, entry_id: UUID) -> bool:
        """Assert that an activity report entry exists in the repository."""
        return self.exists(entry_id)

    def assert_entries_count_for_portfolio(self, portfolio_id: UUID, expected_count: int) -> bool:
        """Assert the number of activity report entries for a portfolio."""
        entries = self.find_by_portfolio_id(portfolio_id)
        return len(entries) == expected_count

    def assert_entries_count_by_type(self, portfolio_id: UUID, activity_type: str, expected_count: int) -> bool:
        """Assert the number of activity report entries for a portfolio by activity type."""
        entries = self.find_by_portfolio_id(portfolio_id, activity_type=activity_type)
        return len(entries) == expected_count

    def assert_method_called(self, method_name: str, times: int = None) -> bool:
        """Assert that a method was called a specific number of times."""
        calls = [call for call in self._call_history if call['method'] == method_name]
        if times is None:
            return len(calls) > 0
        return len(calls) == times

    def assert_entries_in_date_range(self, portfolio_id: UUID, start_date: str, end_date: str, expected_count: int) -> bool:
        """Assert the number of entries in a specific date range."""
        entries = self.find_by_date_range(portfolio_id, start_date, end_date)
        return len(entries) == expected_count

    def get_call_history(self) -> List[dict]:
        """Get the history of method calls for testing."""
        return self._call_history

    def clear_call_history(self):
        """Clear the call history for testing."""
        self._call_history = []

    def clear_data(self):
        """Clear all activity report entry data for testing."""
        self._entries.clear()
        self.clear_call_history()

    def get_entry_count(self) -> int:
        """Get the total number of activity report entries in the repository."""
        return len(self._entries)
