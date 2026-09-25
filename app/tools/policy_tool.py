"""Policy retrieval tool for FAISS knowledge base search."""

import logging
from typing import List, Dict, Any
from app.rag.retriever import search_policy

logger = logging.getLogger(__name__)


def search_company_policy(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search company policy documents in the FAISS vector database.
    
    Args:
        query: Query string.
        top_k: Number of chunks to retrieve.
        
    Returns:
        List of dictionaries with text, source, page, department, and score.
    """
    return search_policy(query=query, top_k=top_k)


# Re-export search_policy directly for consistency with requirements
__all__ = ["search_policy", "search_company_policy"]
