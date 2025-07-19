# Portfolio Import Job Domain Model

## Purpose
This document defines the `PortfolioImportJob` domain model, which extends the `Job` model to handle portfolio import-specific functionality. It includes repository and service implementations.

---

## 1. Domain Model

### Entity: PortfolioImportJob
- Inherits from `Job`.
- Additional Attributes:
  - `portfolio_id: UUID`  
    Identifier for the portfolio associated with the import job.
  - `interval: daterange`  
    PostgreSQL `daterange` representing the time interval of the import.
  - `source: SourceEnum`  
    Enum representing the source of the import (`IBKR`, etc.).

---

## 2. Repository

### PortfolioImportJobRepository
- Methods:
  - `save(job: PortfolioImportJob) -> None`  
    Persists the job to the database.
  - `find_by_id(job_id: UUID) -> Optional[PortfolioImportJob]`  
    Retrieves a job by its ID.
  - `exists_for_interval(portfolio_id: UUID, interval: daterange) -> bool`  
    Checks if a job exists for the given portfolio and interval.

---

## 3. Service

### PortfolioImportJobService
- Methods:
  - `create_job(portfolio_id: UUID, interval: daterange, source: SourceEnum) -> PortfolioImportJob`  
    Creates a new portfolio import job.
  - `mark_as_succeeded(job_id: UUID) -> None`  
    Updates the job status to `Succeeded`.
  - `mark_as_failed(job_id: UUID, error: dict) -> None`  
    Updates the job status to `Failed` and records the error.

---

## 4. Domain Events

### PortfolioImportJobSucceeded
- Triggered when a portfolio import job completes successfully.
- Attributes:
  - `job_id: UUID`
  - `portfolio_id: UUID`
  - `timestamp: datetime`

### PortfolioImportJobFailed
- Triggered when a portfolio import job fails.
- Attributes:
  - `job_id: UUID`
  - `portfolio_id: UUID`
  - `error: dict`
  - `timestamp: datetime`

---

## 5. Relationships
- `PortfolioImportJob` is a subclass of `Job`.
- The repository and service interact with the database and application layer to manage portfolio import jobs.
