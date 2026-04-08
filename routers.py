from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    ServiceMemberCreate,
    ServiceMemberRead,
    UserRead,
    ServiceProfileRead,
    AccountCreate,
    AccountRead,
    TransactionRead,
)
from models import User, ServiceProfile, Account, Transaction, AccountType
from services import (
    create_user_with_service_profile,
    create_account_for_user,
    process_transfer,
    create_system_account,
)

# Routers
service_members_router = APIRouter(prefix="/service-members", tags=["Service Members"])
accounts_router = APIRouter(prefix="/accounts", tags=["Accounts"])
transactions_router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ============================================================================
# SERVICE MEMBERS ENDPOINTS
# ============================================================================

@service_members_router.post("/register", response_model=ServiceMemberRead, status_code=status.HTTP_201_CREATED)
def register_service_member(
    member_data: ServiceMemberCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new service member with their profile.

    Creates both User and ServiceProfile records.
    """
    try:
        user = create_user_with_service_profile(
            db=db,
            name=member_data.name,
            email=member_data.email,
            service_branch=member_data.service_branch,
            rank=member_data.rank,
            current_base_location=member_data.current_base_location,
            is_deployed=member_data.is_deployed,
            deployment_zone=member_data.deployment_zone
        )

        # Return the full service member profile
        return ServiceMemberRead(
            user=UserRead.model_validate(user),
            service_profile=ServiceProfileRead.model_validate(user.service_profile),
            accounts=[]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@service_members_router.get("/{user_id}", response_model=ServiceMemberRead)
def get_service_member(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a service member's full profile including accounts.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service member not found"
        )

    if not user.service_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service profile not found for this user"
        )

    return ServiceMemberRead(
        user=UserRead.model_validate(user),
        service_profile=ServiceProfileRead.model_validate(user.service_profile),
        accounts=[AccountRead.model_validate(acc) for acc in user.accounts]
    )


# ============================================================================
# ACCOUNTS ENDPOINTS
# ============================================================================

@accounts_router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    user_id: int,
    account_data: AccountCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new account for a user.

    Allowed account types: 'main_checking', 'deployment_savings', 'system_deposit'
    """
    try:
        account = create_account_for_user(
            db=db,
            user_id=user_id,
            account_name=account_data.account_name,
            account_type=account_data.account_type
        )
        return AccountRead.model_validate(account)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@accounts_router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    Get account details including current balance.
    """
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return AccountRead.model_validate(account)


@accounts_router.get("/user/{user_id}", response_model=list[AccountRead])
def get_user_accounts(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all accounts for a user.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    return [AccountRead.model_validate(acc) for acc in accounts]


# ============================================================================
# TRANSACTIONS ENDPOINTS
# ============================================================================

@transactions_router.post("/transfer", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def execute_transfer(
    sender_account_id: int,
    receiver_account_id: int,
    amount: float,
    metadata: dict = None,
    db: Session = Depends(get_db)
):
    """
    Execute a transfer between two accounts.

    This uses the double-entry ledger system:
    - Creates one DEBIT entry in the sender's account
    - Creates one CREDIT entry in the receiver's account
    - The transaction is atomic (all-or-nothing)

    Args:
        sender_account_id: Account to debit
        receiver_account_id: Account to credit
        amount: Amount to transfer (must be positive)
        metadata: Optional metadata about the transfer
    """
    try:
        transaction = process_transfer(
            db=db,
            sender_account_id=sender_account_id,
            receiver_account_id=receiver_account_id,
            amount=amount,
            metadata=metadata or {}
        )
        return TransactionRead.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@transactions_router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a transaction and its associated ledger entries.
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return TransactionRead.model_validate(transaction)


@transactions_router.get("/account/{account_id}", response_model=list[TransactionRead])
def get_account_transactions(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all transactions for an account.
    """
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Get all transactions where this account has ledger entries
    transactions = (
        db.query(Transaction)
        .join(Transaction.ledger_entries)
        .filter(Transaction.ledger_entries.any(account_id=account_id))
        .all()
    )

    return [TransactionRead.model_validate(t) for t in transactions]
