"""Indexing script to extract, chunk, embed, and store company policy documents in FAISS."""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

from app.rag.loader import load_all_documents
from app.rag.chunker import chunk_documents
from app.rag.embeddings import embed_documents
from app.rag.vectorstore import save_vectorstore

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rag.indexer")

DEFAULT_DOCS_DIR = os.getenv("DOCUMENTS_DIR", "data/documents")
DEFAULT_VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "data/vectorstore")


def run_indexing(docs_dir: str = DEFAULT_DOCS_DIR, vectorstore_dir: str = DEFAULT_VECTORSTORE_DIR) -> int:
    """Execute the complete indexing pipeline:
    1. Load all PDFs from data/documents/
    2. Split text into chunks and assign metadata
    3. Generate embeddings using SentenceTransformer
    4. Build FAISS index (inner product for normalized cosine similarity)
    5. Save index and metadata to data/vectorstore/
    """
    logger.info("=" * 60)
    logger.info("Starting Enterprise Policy Assistant Document Indexing Pipeline")
    logger.info(f"Source Directory: {docs_dir}")
    logger.info(f"Target Vectorstore Directory: {vectorstore_dir}")
    logger.info("=" * 60)

    # Step 1: Load documents
    pages = load_all_documents(docs_dir)
    if not pages:
        logger.error(f"No pages extracted from {docs_dir}. Please ensure policy PDFs exist.")
        return 0

    # Step 2: Chunk documents
    chunks = chunk_documents(pages, chunk_size=500, chunk_overlap=100)
    if not chunks:
        logger.error("No chunks produced from documents.")
        return 0

    # Step 3: Embed chunks
    texts = [c["text"] for c in chunks]
    logger.info(f"Computing embeddings for {len(texts)} semantic chunks...")
    embeddings = embed_documents(texts)
    dim = embeddings.shape[1]
    logger.info(f"Generated embeddings with dimension: {dim}")

    # Step 4: Create FAISS index
    import faiss
    logger.info("Constructing FAISS IndexFlatIP (Cosine Similarity)...")
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    logger.info(f"FAISS index built. Total indexed vectors: {index.ntotal}")

    # Step 5: Save index and metadata
    save_vectorstore(index, chunks, vectorstore_dir=vectorstore_dir)
    logger.info("=" * 60)
    logger.info(f"SUCCESS: Indexed {len(chunks)} chunks across {len(set(c['source'] for c in chunks))} policy documents.")
    logger.info("=" * 60)
    return index.ntotal


if __name__ == "__main__":
    count = run_indexing()
    if count == 0:
        sys.exit(1)
