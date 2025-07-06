# Tenant Domain (DDD)

## Purpose
This document defines the Tenant domain for the Portfolio Tracker application, following strict Domain Driven Design (DDD) principles. It describes the tenant domain model, value objects, and how tenants support multi-tenant scenarios.

---

## 1. Domain Model

### Entity: Tenant
- `id: UUID`
- `name: str`
- `is_active: bool`  # Indicates soft deletion/deactivation. When False, the tenant is considered deactivated but not physically removed from the database.
- `created_at: datetime`
- `updated_at: datetime`

---

## Value Objects

### TenantName (Value Object)
Encapsulates validation and normalization for tenant names.

**Example (Python, conceptual):**
```python
class TenantName:
    MAX_LENGTH = 100

    def __init__(self, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Tenant name cannot be empty")
        if len(value) > self.MAX_LENGTH:
            raise ValueError(f"Tenant name must be at most {self.MAX_LENGTH} characters")
        self.value = value

    def __str__(self):
        return self.value

    def __eq__(self, other):
        return isinstance(other, TenantName) and self.value == other.value
```

## Aggregates

Tenant is an aggregate root. The following boundaries and invariants must be maintained:

### Tenant Aggregate Invariants
- A tenant’s identity (id) is unique.
- A tenant can only be activated or deactivated through the Tenant aggregate root.
- Only active tenants can have users added to them.
- Tenant properties (e.g., name) can only be changed through the Tenant aggregate root.

### Transactional Boundaries
- All changes to a Tenant (including domain events and user membership changes) should occur in a single transaction, and only through the Tenant aggregate root.

---


## Domain Events

There are currently no tenant domain events because there is no expectation for multi-tenancy. The only tenant will be the default tenant, which simplifies the domain and event model. If multi-tenancy is introduced in the future, domain events such as `TenantCreated`, `TenantDeactivated`, and `TenantNameChanged` can be added as needed.

---

## Repository Layer

### Interface
```python
class TenantRepository(Protocol):
    def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]: ...
    def get_by_name(self, name: str) -> Optional[Tenant]: ...
    def add(self, tenant: Tenant) -> None: ...
    def list(self) -> List[Tenant]: ...
```

---

## Service Layer

- **TenantService**: Tenant creation, activation/deactivation, listing.

---

## References
- [Domain Driven Design Reference](https://domainlanguage.com/ddd/reference/)
