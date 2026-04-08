from fastapi import FastAPI
from fastapi.responses import JSONResponse
from database import Base, engine
from routers import service_members_router, accounts_router, transactions_router

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Blue Light Financial API",
    description="Secure fintech backend for military and emergency services personnel",
    version="1.0.0"
)

# Include routers
app.include_router(service_members_router)
app.include_router(accounts_router)
app.include_router(transactions_router)


@app.get("/")
def read_root():
    """
    Root endpoint. API is ready.
    """
    return {
        "message": "Blue Light Financial API",
        "version": "1.0.0",
        "description": "Secure fintech backend with double-entry ledger"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
