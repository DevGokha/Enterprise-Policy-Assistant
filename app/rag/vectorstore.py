"""FAISS Vector Store manager for indexing and querying policy embeddings."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_VECTORSTORE_DIR = "data/vectorstore"
INDEX_FILENAME = "index.faiss"
METADATA_FILENAME = "metadata.json"

_VECTORSTORE_CACHE: Dict[str, Any] = {}


def save_vectorstore(
    index,
    chunks: List[Dict[str, Any]],
    vectorstore_dir: str = DEFAULT_VECTORSTORE_DIR
) -> None:
    """Persist FAISS index and chunk metadata to disk.
    
    Args:
        index: faiss index instance.
        chunks: List of chunk metadata dictionaries.
        vectorstore_dir: Directory path where index and metadata are saved.
    """
    import faiss
    store_path = Path(vectorstore_dir)
    store_path.mkdir(parents=True, exist_ok=True)

    index_file = store_path / INDEX_FILENAME
    metadata_file = store_path / METADATA_FILENAME

    logger.info(f"Writing FAISS index to {index_file} ({index.ntotal} vectors)...")
    faiss.write_index(index, str(index_file))

    logger.info(f"Writing metadata to {metadata_file} ({len(chunks)} entries)...")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    # Invalidate cache
    _VECTORSTORE_CACHE.clear()
    logger.info("Vector store successfully saved.")


def load_vectorstore(
    vectorstore_dir: str = DEFAULT_VECTORSTORE_DIR
) -> Optional[Tuple[Any, List[Dict[str, Any]]]]:
    """Load FAISS index and chunk metadata from disk.
    
    Args:
        vectorstore_dir: Directory containing index.faiss and metadata.json.
        
    Returns:
        Tuple of (faiss_index, metadata_list) or None if files do not exist.
    """
    global _VECTORSTORE_CACHE
    if "index" in _VECTORSTORE_CACHE and "metadata" in _VECTORSTORE_CACHE:
        return _VECTORSTORE_CACHE["index"], _VECTORSTORE_CACHE["metadata"]

    import faiss
    store_path = Path(vectorstore_dir)
    index_file = store_path / INDEX_FILENAME
    metadata_file = store_path / METADATA_FILENAME

    if not index_file.exists() or not metadata_file.exists():
        logger.warning(f"Vector store files not found in {vectorstore_dir}")
        return None

    try:
        logger.info(f"Loading FAISS index from {index_file}...")
        index = faiss.read_index(str(index_file))

        logger.info(f"Loading metadata from {metadata_file}...")
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        _VECTORSTORE_CACHE["index"] = index
        _VECTORSTORE_CACHE["metadata"] = metadata
        logger.info(f"Vector store loaded successfully with {index.ntotal} items.")
        return index, metadata
    except Exception as e:
        logger.error(f"Error loading vector store from {vectorstore_dir}: {e}")
        return None


def search_vectorstore(
    query_vector: np.ndarray,
    top_k: int = 5,
    vectorstore_dir: str = DEFAULT_VECTORSTORE_DIR
) -> List[Dict[str, Any]]:
    """Query the FAISS vectorstore using a normalized query vector.
    
    Args:
        query_vector: 1D or 2D numpy array of normalized query embedding.
        top_k: Number of nearest neighbors to retrieve.
        vectorstore_dir: Directory of the vector store.
        
    Returns:
        List of matched chunks with cosine similarity score and metadata.
    """
    store = load_vectorstore(vectorstore_dir)
    if not store:
        logger.error("Vectorstore is not initialized or indexed.")
        return []

    index, metadata = store
    if query_vector.ndim == 1:
        query_vector = np.expand_dims(query_vector, axis=0).astype(np.float32)

    # Search index
    scores, indices = index.search(query_vector, min(top_k, index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0 and idx < len(metadata):
            item = dict(metadata[idx])
            item["score"] = float(score)  # Cosine similarity when vectors are normalized
            results.append(item)

    return results
