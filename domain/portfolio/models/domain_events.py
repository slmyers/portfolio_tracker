from uuid import UUID
from datetime import datetime
from core.domain_event import DomainEvent

class PortfolioImportJobSucceeded(DomainEvent):
    def __init__(self, job_id: UUID, portfolio_id: UUID, timestamp: datetime):
        self.job_id = job_id
        self.portfolio_id = portfolio_id
        self.timestamp = timestamp

    def __repr__(self):
        return f"PortfolioImportJobSucceeded(job_id={self.job_id}, portfolio_id={self.portfolio_id}, timestamp={self.timestamp})"

class PortfolioImportJobFailed(DomainEvent):
    def __init__(self, job_id: UUID, portfolio_id: UUID, error: dict, timestamp: datetime):
        self.job_id = job_id
        self.portfolio_id = portfolio_id
        self.error = error
        self.timestamp = timestamp

    def __repr__(self):
        return f"PortfolioImportJobFailed(job_id={self.job_id}, portfolio_id={self.portfolio_id}, error={self.error}, timestamp={self.timestamp})"
