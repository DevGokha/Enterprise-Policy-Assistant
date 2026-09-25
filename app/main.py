"""Main FastAPI application for TechNova Enterprise Policy Assistant."""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.database.database import init_db
from app.database.seed import seed_database
from app.api.chat import router as api_router
from app.rag.vectorstore import load_vectorstore

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("enterprise.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to initialize database and check vectorstore on startup."""
    logger.info("Initializing Enterprise Policy Assistant application...")
    try:
        init_db()
        # Check if database is empty, if so seed sample records
        from app.database.database import SessionLocal
        from app.database.models import Employee
        db = SessionLocal()
        if db.query(Employee).count() == 0:
            logger.info("Database is empty. Running initial seed...")
            seed_database()
        db.close()
    except Exception as e:
        logger.error(f"Database startup error: {e}")

    # Check vectorstore presence
    store = load_vectorstore()
    if store:
        logger.info("FAISS vector store loaded successfully.")
    else:
        logger.warning("FAISS vector store not yet indexed. Run 'python -m app.rag.index' or POST /api/index")

    yield
    logger.info("Shutting down Enterprise Policy Assistant application.")


app = FastAPI(
    title="TechNova Enterprise Policy Assistant API",
    description="Enterprise AI Assistant providing RAG policy knowledge retrieval and Agentic HR actions with safety guardrails.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router)


@app.get("/")
def root():
    """Welcome endpoint providing service metadata."""
    return {
        "service": "TechNova Enterprise Policy Assistant",
        "organization": "TechNova Solutions Pvt. Ltd.",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "features": [
            "Policy Q&A with RAG Grounding and Citations",
            "Single-Agent LangGraph HR Workflow",
            "Employee Profile & Leave Balance Management",
            "Confirmation Safety Guardrails for State Changes"
        ]
    }


@app.get("/health")
def health():
    """Health check endpoint verifying database connectivity and vectorstore availability."""
    db_status = "connected"
    try:
        from app.database.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    store = load_vectorstore()
    vs_status = "indexed" if store else "not_indexed"
    vector_count = store[0].ntotal if store else 0

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "vectorstore": {
            "status": vs_status,
            "total_vectors": vector_count
        },
        "model": os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    }
