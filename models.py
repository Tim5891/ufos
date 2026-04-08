from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
import enum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    service_profile = relationship("ServiceProfile", back_populates="user", uselist=False)
    accounts = relationship("Account", back_populates="user")


class ServiceProfile(Base):
    __tablename__ = "service_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    service_branch = Column(String(100), nullable=False)  # Army, Navy, NHS, Police, etc.
    rank = Column(String(100), nullable=False)
    current_base_location = Column(String(255), nullable=False)
    is_deployed = Column(Boolean, default=False)
    deployment_zone = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="service_profile")


class AccountType(str, enum.Enum):
    MAIN_CHECKING = "main_checking"
    DEPLOYMENT_SAVINGS = "deployment_savings"
    SYSTEM_DEPOSIT = "system_deposit"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for system accounts
    account_name = Column(String(100), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    balance = Column(Float, default=0.0)
    is_system_account = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="accounts")
    ledger_entries = relationship("LedgerEntry", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(50), nullable=False)  # 'transfer', 'deposit', 'withdrawal', etc.
    amount = Column(Float, nullable=False)
    metadata = Column(Text, nullable=True)  # JSON-serialized metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ledger_entries = relationship("LedgerEntry", back_populates="transaction")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    entry_type = Column(String(10), nullable=False)  # 'debit' or 'credit'
    amount = Column(Float, nullable=False)  # Always positive; entry_type determines direction
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    transaction = relationship("Transaction", back_populates="ledger_entries")
    account = relationship("Account", back_populates="ledger_entries")
