"""Document chunking and metadata enrichment module."""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def split_text_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks respecting paragraph and sentence boundaries.
    
    Args:
        text: Raw document text.
        chunk_size: Maximum target chunk length in characters.
        chunk_overlap: Overlap between consecutive chunks.
        
    Returns:
        List of text chunks.
    """
    if not text:
        return []

    # First split by paragraphs
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If adding paragraph exceeds chunk_size, split further or flush
        if len(current_chunk) + len(para) + 1 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{para}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
                # Keep overlap from the end of current_chunk
                overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                current_chunk = f"{overlap_text}\n\n{para}".strip()
            else:
                # Single paragraph is longer than chunk_size, split by sentences or line
                sentences = re.split(r'(?<=[.!?])\s+', para)
                sub_chunk = ""
                for s in sentences:
                    if len(sub_chunk) + len(s) + 1 <= chunk_size:
                        sub_chunk = f"{sub_chunk} {s}".strip()
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                            sub_chunk = s
                        else:
                            # Sentence itself is longer than chunk_size, hard chunk
                            for i in range(0, len(s), chunk_size - chunk_overlap):
                                chunks.append(s[i:i + chunk_size])
                            sub_chunk = ""
                if sub_chunk:
                    current_chunk = sub_chunk

    if current_chunk and (not chunks or chunks[-1] != current_chunk):
        chunks.append(current_chunk)

    return chunks


def chunk_documents(
    pages: List[Dict[str, Any]],
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> List[Dict[str, Any]]:
    """Chunk all document pages and attach rich enterprise metadata.
    
    Args:
        pages: List of page objects from loader.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap between chunks.
        
    Returns:
        List of chunk objects with enriched metadata:
        {
            "chunk_id": "leave_023",
            "text": "...",
            "source": "leave_policy.pdf",
            "page": 6,
            "department": "HR",
            "policy_version": "2.1",
            "document_type": "Leave Policy"
        }
    """
    all_chunks = []
    chunk_counters: Dict[str, int] = {}

    for page_data in pages:
        source = page_data["source"]
        page_num = page_data["page"]
        text = page_data["text"]

        prefix = source.replace(".pdf", "").replace("_policy", "").lower()
        if prefix not in chunk_counters:
            chunk_counters[prefix] = 1

        text_chunks = split_text_into_chunks(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for chunk_text in text_chunks:
            chunk_num = chunk_counters[prefix]
            chunk_counters[prefix] += 1

            chunk_id = f"{prefix}_{chunk_num:03d}"
            all_chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "source": source,
                "page": page_num,
                "department": page_data.get("department", "HR"),
                "policy_version": page_data.get("policy_version", "1.0"),
                "document_type": page_data.get("document_type", "Corporate Policy")
            })

    logger.info(f"Chunked {len(pages)} pages into {len(all_chunks)} semantic chunks.")
    return all_chunks
