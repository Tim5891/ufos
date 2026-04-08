from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from models import AccountType


# User Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# Service Profile Schemas
class ServiceProfileCreate(BaseModel):
    service_branch: str
    rank: str
    current_base_location: str
    is_deployed: bool = False
    deployment_zone: Optional[str] = None


class ServiceProfileRead(BaseModel):
    id: int
    user_id: int
    service_branch: str
    rank: str
    current_base_location: str
    is_deployed: bool
    deployment_zone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Account Schemas
class AccountCreate(BaseModel):
    account_name: str
    account_type: AccountType


class AccountRead(BaseModel):
    id: int
    user_id: Optional[int]
    account_name: str
    account_type: AccountType
    balance: float
    is_system_account: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Transaction & Ledger Entry Schemas
class LedgerEntryRead(BaseModel):
    id: int
    transaction_id: int
    account_id: int
    entry_type: str  # 'debit' or 'credit'
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionRead(BaseModel):
    id: int
    transaction_type: str
    amount: float
    metadata: Optional[str]
    created_at: datetime
    ledger_entries: list[LedgerEntryRead]

    class Config:
        from_attributes = True


# Service Member Profile Schemas (combines User + ServiceProfile)
class ServiceMemberCreate(BaseModel):
    name: str
    email: EmailStr
    service_branch: str
    rank: str
    current_base_location: str
    is_deployed: bool = False
    deployment_zone: Optional[str] = None


class ServiceMemberRead(BaseModel):
    user: UserRead
    service_profile: ServiceProfileRead
    accounts: list[AccountRead]

    class Config:
        from_attributes = True
