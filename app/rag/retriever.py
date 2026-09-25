"""Retriever module providing semantic search over company policy documents."""

import logging
from typing import List, Dict, Any
from app.rag.embeddings import embed_text
from app.rag.vectorstore import search_vectorstore

logger = logging.getLogger(__name__)


def search_policy(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search company policy documents for relevant context using semantic search.
    
    Args:
        query: User question or natural language query.
        top_k: Number of top results to return (default: 5).
        
    Returns:
        List of relevant policy chunks with source, page, text, department, document_type, and score.
    """
    if not query or not query.strip():
        logger.warning("Empty search query provided to search_policy.")
        return []

    logger.info(f"Searching policy documents for query: '{query}' (top_k={top_k})")
    try:
        query_vec = embed_text(query.strip())
        results = search_vectorstore(query_vec, top_k=top_k)
        logger.info(f"Retrieved {len(results)} matching chunks.")
        return results
    except Exception as e:
        logger.error(f"Error in search_policy: {e}")
        return []
