#!/usr/bin/env bash
# Script to run TechNova Enterprise Policy Assistant (FastAPI + Streamlit)
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

export PYTHONPATH=.

echo "============================================================"
echo "Starting TechNova Enterprise Policy Assistant Services"
echo "============================================================"

# Ensure database is seeded and documents are indexed
if [ ! -f "data/enterprise.db" ]; then
    echo "[1/3] Seeding SQLite database..."
    python -m app.database.seed
fi

if [ ! -f "data/vectorstore/index.faiss" ]; then
    echo "[2/3] Generating documents and building FAISS index..."
    python -m data.generate_documents
    python -m app.rag.index
fi

echo "[3/3] Launching FastAPI backend and Streamlit UI..."
echo "  - FastAPI Swagger Docs: http://localhost:8000/docs"
echo "  - Streamlit Dashboard:  http://localhost:8501"
echo "============================================================"

# Start FastAPI in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!

# Trap signals to cleanly kill both processes on Ctrl+C
trap "echo 'Stopping services...'; kill $FASTAPI_PID 2>/dev/null; exit 0" INT TERM EXIT

# Start Streamlit in foreground
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
