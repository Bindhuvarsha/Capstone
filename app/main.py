"""
MigrateIQ Backend Application Entrypoint
FastAPI application serving Ask, Scan, Decisions, and Plan APIs.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.core.database import init_db
from app.api import ask_router, scan_router, decisions_router, plan_router
from app.ingestion.vector_store import VectorStore

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    init_db()
    # Ensure vector store is initialized
    yield

# Ensure tables are created on module import
init_db()

app = FastAPI(
    title="MigrateIQ: AI Co-pilot for ECC to S/4HANA Migration",
    description="Agentic AI assistant helping SAP consultants and developers plan ECC to S/4HANA migrations.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck Endpoint
@app.get("/api/v1/health", tags=["Health"])
def healthcheck():
    store = VectorStore()
    return {
        "status": "healthy",
        "app": "MigrateIQ",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "sqlite_connected",
        "vector_store_chunks": store.count()
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to MigrateIQ API",
        "docs_url": "/docs",
        "health_url": "/api/v1/health"
    }

# Register API Routers
app.include_router(ask_router, prefix=settings.API_PREFIX)
app.include_router(scan_router, prefix=settings.API_PREFIX)
app.include_router(decisions_router, prefix=settings.API_PREFIX)
app.include_router(plan_router, prefix=settings.API_PREFIX)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
