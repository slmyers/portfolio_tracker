# User Domain (DDD)

## Purpose
This document defines the User domain for the Portfolio Tracker application, following strict Domain Driven Design (DDD) principles. It describes the user domain model, value objects, and how users interact with tenants in a multi-tenant scenario.

---

## 1. Domain Model


### Entity: User
- `id: UUID`
- `tenant_id: UUID`
- `email: Email`  # Value Object
- `name: str`
- `password_hash: PasswordHash`  # Value Object
- `role: Role`  # Value Object (see below for valid roles)

#### Valid Roles
The `Role` value object supports the following valid roles (must match both code and database enum):

- `user`
- `admin`
- `system`
- `super_admin`
- `auditor`

- `is_active: bool`  # Indicates soft deletion/deactivation. When False, the user is considered deactivated but not physically removed from the database.
- `created_at: datetime`
- `updated_at: datetime`

---

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

## Value Objects

Value objects encapsulate domain rules and validation for specific fields. In the User domain, the following value objects are used:

### Email (Value Object)
Encapsulates email address validation and normalization.

**Example (Python, conceptual):**
```python
import re

class Email:
    EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    def __init__(self, value: str):
        value = value.strip().lower()
        if not re.match(self.EMAIL_REGEX, value):
            raise ValueError(f"Invalid email: {value}")
        self.value = value
    def __str__(self):
        return self.value
    def __eq__(self, other):
        return isinstance(other, Email) and self.value == other.value
```

### PasswordHash (Value Object)
Encapsulates password hashing and verification logic.

**Example (Python, conceptual):**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class PasswordHash:
    def __init__(self, hashed: str):
        self.hashed = hashed
    @staticmethod
    def create(plain_password: str) -> "PasswordHash":
        return PasswordHash(pwd_context.hash(plain_password))
    def verify(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.hashed)
```

### Role (Value Object)
Restricts role values to a known set and enforces invariants.

**Example (Python, conceptual):**
```python
class Role:
    VALID_ROLES = {"user", "admin", "system", "super_admin", "auditor"}
    def __init__(self, value: str):
        value = value.lower()
        if value not in self.VALID_ROLES:
            raise ValueError(f"Invalid role: {value}. Must be one of {self.VALID_ROLES}")
        self.value = value
    def __str__(self):
        return self.value
    def __eq__(self, other):
        return isinstance(other, Role) and self.value == other.value
```

---


## Aggregates

User is an aggregate root. The following boundaries and invariants must be maintained:

### User Aggregate Invariants
- A user’s identity (id) is unique within the system.
- A user must always belong to a valid, active tenant.
- User creation, removal, or role changes must be performed through the User aggregate root.
- User email and role must be valid according to their value object rules.
- A user cannot be created or reactivated if their tenant is inactive.

### Transactional Boundaries
- All changes to a User (including domain events) should occur in a single transaction, and only through the User aggregate root.
- Cross-aggregate operations (e.g., creating a user and updating a tenant) should be coordinated at the service/application layer, not within aggregates themselves.

---


## Domain Events

The system supports multiple users. The primary user domain events are:

- UserAdded
- UserRemoved
- UserRoleChanged

Additional events such as `UserPasswordChanged` can be introduced as the domain evolves.

---

## Repository Layer

### Interface
```python
class UserRepository(Protocol):
    def get_by_id(self, user_id: UUID) -> Optional[User]: ...
    def get_by_email(self, email: str) -> Optional[User]: ...
    def add(self, user: User) -> None: ...
    def list_by_tenant(self, tenant_id: UUID) -> List[User]: ...
```

---

## Service Layer

- **UserService**: Registration, authentication, user management.

---

## References
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [passlib documentation](https://passlib.readthedocs.io/en/stable/)
