from core.job import Job, JobStatus
from uuid import UUID
from datetime import datetime
from typing import Optional
from domain.portfolio.models.domain_events import PortfolioImportJobSucceeded, PortfolioImportJobFailed

class PortfolioImportJob(Job):
    def __init__(self, portfolio_id: UUID, interval: str, source: str, id: UUID, status: JobStatus, created_at: datetime, updated_at: datetime, error: Optional[dict] = None):
        super().__init__(id=id, status=status, created_at=created_at, updated_at=updated_at, error=error)
        self.portfolio_id = portfolio_id
        self.interval = interval
        self.source = source

    def mark_as_succeeded(self):
        super().mark_as_succeeded()
        self.record_event(PortfolioImportJobSucceeded(job_id=self.id, portfolio_id=self.portfolio_id, timestamp=datetime.now()))

    def mark_as_failed(self, error: dict):
        super().mark_as_failed(error)
        self.record_event(PortfolioImportJobFailed(job_id=self.id, portfolio_id=self.portfolio_id, error=error, timestamp=datetime.now()))

    def __repr__(self):
        return f"PortfolioImportJob(portfolio_id={self.portfolio_id}, interval={self.interval}, source={self.source}, id={self.id}, status={self.status}, created_at={self.created_at}, updated_at={self.updated_at}, error={self.error})"
