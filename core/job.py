from enum import Enum
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
from core.domain_model import DomainModel

class JobStatus(Enum):
    PENDING = "Pending"
    IN_PROGRESS = "InProgress"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"

class Job(DomainModel):
    def __init__(self, id: UUID, status: JobStatus, created_at: datetime, updated_at: datetime, error: Optional[Dict] = None):
        super().__init__()
        self.id = id
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.error = error

    def mark_as_succeeded(self):
        if self.status != JobStatus.IN_PROGRESS:
            raise ValueError("Job must be in progress to mark as succeeded.")
        self.status = JobStatus.SUCCEEDED
        self.updated_at = datetime.now()

    def mark_as_failed(self, error: Dict):
        if self.status != JobStatus.IN_PROGRESS:
            raise ValueError("Job must be in progress to mark as failed.")
        self.status = JobStatus.FAILED
        self.error = error
        self.updated_at = datetime.now()

    def __repr__(self):
        return f"Job(id={self.id}, status={self.status}, created_at={self.created_at}, updated_at={self.updated_at}, error={self.error})"
