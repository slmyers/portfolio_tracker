import unittest
from uuid import uuid4
from datetime import datetime
from core.job import JobStatus
from domain.portfolio.models.portfolio_import_job import PortfolioImportJob
from domain.portfolio.models.domain_events import PortfolioImportJobSucceeded, PortfolioImportJobFailed

class TestPortfolioImportJob(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid4()
        self.interval = "[2025-01-01,2025-06-30]"
        self.source = "IBKR"
        self.job_id = uuid4()
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.job = PortfolioImportJob(portfolio_id=self.portfolio_id, interval=self.interval, source=self.source, id=self.job_id, status=JobStatus.PENDING, created_at=self.created_at, updated_at=self.updated_at)

    def test_initialization(self):
        self.assertEqual(self.job.portfolio_id, self.portfolio_id)
        self.assertEqual(self.job.interval, self.interval)
        self.assertEqual(self.job.source, self.source)
        self.assertEqual(self.job.id, self.job_id)
        self.assertEqual(self.job.status, JobStatus.PENDING)
        self.assertEqual(self.job.created_at, self.created_at)
        self.assertEqual(self.job.updated_at, self.updated_at)
        self.assertIsNone(self.job.error)

    def test_mark_as_succeeded(self):
        self.job.status = JobStatus.IN_PROGRESS
        self.job.mark_as_succeeded()
        self.assertEqual(self.job.status, JobStatus.SUCCEEDED)
        self.assertIsNotNone(self.job.updated_at)

    def test_mark_as_failed(self):
        self.job.status = JobStatus.IN_PROGRESS
        error = {"message": "An error occurred."}
        self.job.mark_as_failed(error)
        self.assertEqual(self.job.status, JobStatus.FAILED)
        self.assertEqual(self.job.error, error)
        self.assertIsNotNone(self.job.updated_at)

    def test_invalid_status_transition_to_succeeded(self):
        with self.assertRaises(ValueError):
            self.job.mark_as_succeeded()

    def test_invalid_status_transition_to_failed(self):
        with self.assertRaises(ValueError):
            self.job.mark_as_failed({"message": "An error occurred."})

    def test_mark_as_succeeded_records_event(self):
        self.job.status = JobStatus.IN_PROGRESS
        self.job.mark_as_succeeded()
        events = self.job.pull_events()
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], PortfolioImportJobSucceeded)
        self.assertEqual(events[0].job_id, self.job.id)
        self.assertEqual(events[0].portfolio_id, self.job.portfolio_id)

    def test_mark_as_failed_records_event(self):
        self.job.status = JobStatus.IN_PROGRESS
        error = {"message": "An error occurred."}
        self.job.mark_as_failed(error)
        events = self.job.pull_events()
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], PortfolioImportJobFailed)
        self.assertEqual(events[0].job_id, self.job.id)
        self.assertEqual(events[0].portfolio_id, self.job.portfolio_id)
        self.assertEqual(events[0].error, error)

if __name__ == "__main__":
    unittest.main()
