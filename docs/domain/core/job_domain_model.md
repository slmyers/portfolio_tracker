# Core Job Domain Model

## Purpose
This document defines the `Job` domain model, which serves as a base entity for various types of jobs in the system. It adheres to strict Domain Driven Design (DDD) principles and focuses solely on the domain model without repository or service implementations.

---

## 1. Domain Model

### Entity: Job
- `id: UUID`  
  Unique identifier for the job.
- `status: JobStatus`  
  Enum representing the current status of the job (`Pending`, `InProgress`, `Succeeded`, `Failed`).
- `error: Optional[dict]`  
  JSON object containing error details if the job fails.
- `created_at: datetime`  
  Timestamp when the job was created.
- `updated_at: datetime`  
  Timestamp when the job was last updated.

---

## 2. Domain Events

### JobSucceeded
- Triggered when a job completes successfully.
- Attributes:
  - `job_id: UUID`
  - `timestamp: datetime`

### JobFailed
- Triggered when a job fails.
- Attributes:
  - `job_id: UUID`
  - `error: dict`
  - `timestamp: datetime`

---

## 3. Invariants
- A job cannot transition directly from `Pending` to `Succeeded` or `Failed`.
- `error` must be `None` unless the job status is `Failed`.

---

## 4. Relationships
- The `Job` entity can be extended by specific job types (e.g., `PortfolioImportJob`).
