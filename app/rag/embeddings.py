"""Embedding service using Sentence Transformers."""

import os
import logging
from typing import List, Union
import numpy as np
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

_MODEL_INSTANCE = None


def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME):
    """Singleton getter for the SentenceTransformer model to prevent reloading into memory."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SentenceTransformer model: {model_name}...")
        _MODEL_INSTANCE = SentenceTransformer(model_name)
        logger.info("SentenceTransformer model loaded successfully.")
    return _MODEL_INSTANCE


def embed_text(text: str, model_name: str = DEFAULT_MODEL_NAME) -> np.ndarray:
    """Generate normalized embedding vector for a single query string.
    
    Args:
        text: Query or sentence string.
        model_name: Hugging Face model identifier.
        
    Returns:
        1D numpy array of shape (embedding_dim,) normalized for cosine similarity.
    """
    model = get_embedding_model(model_name)
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding


def embed_documents(texts: List[str], model_name: str = DEFAULT_MODEL_NAME, batch_size: int = 32) -> np.ndarray:
    """Generate normalized embeddings for a list of document chunks.
    
    Args:
        texts: List of text chunks.
        model_name: Hugging Face model identifier.
        batch_size: Batch size for encoding.
        
    Returns:
        2D numpy array of shape (num_documents, embedding_dim) with normalized vectors.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    model = get_embedding_model(model_name)
    logger.info(f"Encoding {len(texts)} chunks in batches of {batch_size}...")
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    return embeddings.astype(np.float32)
