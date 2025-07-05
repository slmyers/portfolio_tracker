from uuid import UUID
from datetime import datetime
from core.domain_model import DomainModel
from .user_events import UserAdded, UserRemoved, UserRoleChanged
from typing import Optional
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

class PasswordHash:
    def __init__(self, hashed: str):
        self.hashed = hashed
    @staticmethod
    def create(plain_password: str, pwd_context) -> "PasswordHash":
        return PasswordHash(pwd_context.hash(plain_password))
    def verify(self, plain_password: str, pwd_context) -> bool:
        return pwd_context.verify(plain_password, self.hashed)

class Role:
    VALID_ROLES = {"user", "admin"}
    def __init__(self, value: str):
        value = value.lower()
        if value not in self.VALID_ROLES:
            raise ValueError(f"Invalid role: {value}. Must be one of {self.VALID_ROLES}")
        self.value = value
    def __str__(self):
        return self.value
    def __eq__(self, other):
        return isinstance(other, Role) and self.value == other.value

class User(DomainModel):
    def __init__(self, id: UUID, tenant_id: UUID, email: Email, name: str, password_hash: PasswordHash, role: Role, is_active: bool = True, created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None):
        super().__init__()
        self.id = id
        self.tenant_id = tenant_id
        self.email = email
        self.name = name
        self.password_hash = password_hash
        self.role = role
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        # Record event for user creation
        self.record_event(UserAdded(
            user_id=self.id,
            tenant_id=self.tenant_id,
            email=str(self.email),
            occurred_at=self.created_at
        ))
    def deactivate(self):
        if not self.is_active:
            return
        self.is_active = False
        self.updated_at = datetime.utcnow()
        self.record_event(UserRemoved(
            user_id=self.id,
            tenant_id=self.tenant_id,
            occurred_at=self.updated_at
        ))
    def activate(self):
        if self.is_active:
            return
        self.is_active = True
        self.updated_at = datetime.utcnow()
    def change_role(self, new_role: Role, changed_by: Optional[str] = None):
        if self.role == new_role:
            return
        old_role = str(self.role)
        self.role = new_role
        self.updated_at = datetime.utcnow()
        self.record_event(UserRoleChanged(
            user_id=self.id,
            tenant_id=self.tenant_id,
            old_role=old_role,
            new_role=str(new_role),
            changed_by=changed_by,
            occurred_at=self.updated_at
        ))
