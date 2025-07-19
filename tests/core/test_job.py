import unittest
from uuid import uuid4
from datetime import datetime
from core.job import Job, JobStatus

class TestJob(unittest.TestCase):
    def setUp(self):
        self.job_id = uuid4()
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.job = Job(id=self.job_id, status=JobStatus.PENDING, created_at=self.created_at, updated_at=self.updated_at)

    def test_initialization(self):
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

if __name__ == "__main__":
    unittest.main()
