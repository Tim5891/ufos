from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import Account, Transaction, LedgerEntry, User, ServiceProfile, AccountType
from schemas import AccountCreate
import json


def process_transfer(
    db: Session,
    sender_account_id: int,
    receiver_account_id: int,
    amount: float,
    metadata: dict = None
) -> Transaction:
    """
    Execute a transfer between two accounts using double-entry ledger.

    CRITICAL: This function must be ACID compliant. The entire transaction
    rolls back if any operation fails.

    A single Transaction generates exactly two LedgerEntries:
    - One DEBIT from sender account
    - One CREDIT to receiver account

    The sum of all LedgerEntry amounts for this transaction_id = 0
    (amount_debit + (-amount_credit) = 0)

    Args:
        db: SQLAlchemy session
        sender_account_id: ID of account to debit
        receiver_account_id: ID of account to credit
        amount: Amount to transfer (must be positive)
        metadata: Optional dictionary with transaction metadata

    Returns:
        Transaction object with associated LedgerEntries

    Raises:
        ValueError: If validation fails
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validation
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        sender = db.query(Account).filter(Account.id == sender_account_id).first()
        receiver = db.query(Account).filter(Account.id == receiver_account_id).first()

        if not sender:
            raise ValueError(f"Sender account {sender_account_id} not found")
        if not receiver:
            raise ValueError(f"Receiver account {receiver_account_id} not found")

        if sender.balance < amount:
            raise ValueError(f"Insufficient funds. Balance: {sender.balance}, Amount: {amount}")

        # Create the transaction record
        transaction = Transaction(
            transaction_type="transfer",
            amount=amount,
            metadata=json.dumps(metadata) if metadata else None
        )
        db.add(transaction)
        db.flush()  # Get the transaction ID without committing

        # Create DEBIT entry (sender)
        debit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=sender_account_id,
            entry_type="debit",
            amount=amount
        )
        db.add(debit_entry)

        # Create CREDIT entry (receiver)
        credit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=receiver_account_id,
            entry_type="credit",
            amount=amount
        )
        db.add(credit_entry)

        # Update account balances
        sender.balance -= amount
        receiver.balance += amount

        # Commit all changes atomically
        db.commit()
        db.refresh(transaction)

        return transaction

    except ValueError:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Database error during transfer: {str(e)}")
    except Exception as e:
        db.rollback()
        raise ValueError(f"Unexpected error during transfer: {str(e)}")


def create_user_with_service_profile(
    db: Session,
    name: str,
    email: str,
    service_branch: str,
    rank: str,
    current_base_location: str,
    is_deployed: bool = False,
    deployment_zone: str = None
) -> User:
    """
    Create a new service member with User and ServiceProfile.

    Args:
        db: SQLAlchemy session
        name: User's full name
        email: User's email
        service_branch: Military/Emergency service branch
        rank: Service member's rank
        current_base_location: Base location
        is_deployed: Whether currently deployed
        deployment_zone: Current deployment zone if deployed

    Returns:
        User object with associated ServiceProfile
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        # Create user
        user = User(name=name, email=email)
        db.add(user)
        db.flush()

        # Create service profile
        service_profile = ServiceProfile(
            user_id=user.id,
            service_branch=service_branch,
            rank=rank,
            current_base_location=current_base_location,
            is_deployed=is_deployed,
            deployment_zone=deployment_zone
        )
        db.add(service_profile)

        db.commit()
        db.refresh(user)

        return user

    except ValueError:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Database error creating service member: {str(e)}")


def create_account_for_user(
    db: Session,
    user_id: int,
    account_name: str,
    account_type: AccountType
) -> Account:
    """
    Create a new account for a user.

    Args:
        db: SQLAlchemy session
        user_id: User ID
        account_name: Human-readable account name
        account_type: Type of account

    Returns:
        Account object
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        account = Account(
            user_id=user_id,
            account_name=account_name,
            account_type=account_type,
            balance=0.0,
            is_system_account=False
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        return account

    except ValueError:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Database error creating account: {str(e)}")


def create_system_account(
    db: Session,
    account_name: str,
    account_type: AccountType
) -> Account:
    """
    Create a system account (e.g., 'Master Deposit Account').
    System accounts have no associated user.

    Args:
        db: SQLAlchemy session
        account_name: Name of the system account
        account_type: Type of account

    Returns:
        Account object
    """
    try:
        account = Account(
            user_id=None,
            account_name=account_name,
            account_type=account_type,
            balance=0.0,
            is_system_account=True
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        return account

    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Database error creating system account: {str(e)}")
