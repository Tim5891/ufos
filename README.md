# Blue Light Financial API

A secure fintech backend for military and emergency services personnel, built with FastAPI, SQLAlchemy, and PostgreSQL.

## Foundation: Double-Entry Ledger System

This API implements the fundamental principle of fintech: **never just update a balance**. Instead, we use a Double-Entry Ledger where every financial movement is recorded as two balanced entries (debit and credit), ensuring the net change across the entire system is always exactly zero.

## Core Architecture

### 1. Customer Profiles (Task 1)

**User Model**
- `id`: Primary key
- `name`: Full name
- `email`: Unique email address
- `created_at`: Account creation timestamp

**ServiceProfile Model** (tied to User)
- `id`: Primary key
- `user_id`: Foreign key to User
- `service_branch`: Army, Navy, NHS, Police, etc.
- `rank`: Service member's rank
- `current_base_location`: Base location
- `is_deployed`: Boolean flag for deployment status
- `deployment_zone`: Current deployment location (nullable)
- `created_at`: Profile creation timestamp

### 2. Double-Entry Ledger (Task 2)

**Account Model**
- `id`: Primary key
- `user_id`: Foreign key to User (nullable for system accounts)
- `account_name`: Human-readable name (e.g., "Main Checking", "Deployment Savings")
- `account_type`: ENUM (main_checking, deployment_savings, system_deposit)
- `balance`: Current balance
- `is_system_account`: Boolean flag for internal accounts
- `created_at`: Account creation timestamp

**Transaction Model**
- `id`: Primary key
- `transaction_type`: Type of transaction (transfer, deposit, withdrawal, etc.)
- `amount`: Transaction amount
- `metadata`: Optional JSON metadata
- `created_at`: Transaction timestamp

**LedgerEntry Model** (THE CRITICAL PIECE)
- `id`: Primary key
- `transaction_id`: Foreign key to Transaction
- `account_id`: Foreign key to Account
- `entry_type`: 'debit' or 'credit'
- `amount`: Amount (always positive; direction determined by entry_type)
- `created_at`: Entry creation timestamp

**INVARIANT: For any single transaction_id:**
```
SUM(LedgerEntry.amount WHERE entry_type='debit') 
= 
SUM(LedgerEntry.amount WHERE entry_type='credit')
```

This ensures the entire ledger always sums to zero.

### 3. Core Service Logic (Task 3)

#### `process_transfer(sender_account_id, receiver_account_id, amount, metadata)`

This is the heart of the system. It executes a transfer with guaranteed ACID compliance:

1. **Validate**: Check both accounts exist, sender has sufficient funds
2. **Create Transaction**: Record the transfer
3. **Create Entries**: 
   - Debit entry in sender account
   - Credit entry in receiver account
4. **Update Balances**: Decrease sender, increase receiver
5. **Atomic Commit**: All changes commit together, or everything rolls back

If the debit succeeds but the credit fails, the entire transaction is rolled back. No partial transfers.

### 4. API Endpoints (Task 4)

#### Service Members
- `POST /service-members/register` - Register a new service member
- `GET /service-members/{user_id}` - Get full profile with accounts

#### Accounts
- `POST /accounts/` - Create a new account for a user
- `GET /accounts/{account_id}` - Get account details
- `GET /accounts/user/{user_id}` - Get all accounts for a user

#### Transactions
- `POST /transactions/transfer` - Execute a transfer between accounts
- `GET /transactions/{transaction_id}` - Get transaction details
- `GET /transactions/account/{account_id}` - Get account transaction history

## Setup & Installation

### Prerequisites
- Python 3.10+
- PostgreSQL (or Supabase PostgreSQL instance)
- pip

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your database URL
   ```

5. Run the application:
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

## Example: Register a Service Member & Make a Transfer

### 1. Register a Service Member
```bash
curl -X POST http://localhost:8000/service-members/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Captain John Smith",
    "email": "john.smith@army.mil",
    "service_branch": "Army",
    "rank": "Captain",
    "current_base_location": "Fort Bragg",
    "is_deployed": false
  }'
```

### 2. Create an Account for the User
```bash
curl -X POST http://localhost:8000/accounts/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "account_name": "Main Checking",
    "account_type": "main_checking"
  }'
```

### 3. Execute a Transfer
```bash
curl -X POST http://localhost:8000/transactions/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "sender_account_id": 1,
    "receiver_account_id": 2,
    "amount": 100.00,
    "metadata": {"reason": "salary_deposit"}
  }'
```

## Key Security Principles

1. **ACID Compliance**: All transactions are atomic
2. **Double-Entry Verification**: Every transaction creates balanced entries
3. **Audit Trail**: Every debit and credit is recorded
4. **No Direct Balance Updates**: Balances only change through ledger entries
5. **Rollback Safety**: Failed operations never leave partial state

## Files Structure

```
/home/user/ufos/
├── main.py              # FastAPI application entry point
├── database.py          # Database configuration and session management
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic request/response schemas
├── services.py          # Core business logic (process_transfer, etc.)
├── routers.py           # API endpoint routers
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Next Steps

Once this foundation is approved and reviewed, you can build:
- Advanced user authentication & authorization
- Deployment-specific financial rules
- Transaction approval workflows
- Comprehensive audit logging
- Analytics and reporting
- Bank-level security features