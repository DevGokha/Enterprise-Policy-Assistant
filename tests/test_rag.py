"""Unit tests for RAG pipeline: document loader, chunker, vectorstore, and retriever."""

import pytest
from pathlib import Path

from app.rag.loader import load_single_pdf, load_all_documents
from app.rag.chunker import chunk_documents, split_text_into_chunks
from app.rag.vectorstore import load_vectorstore, search_vectorstore
from app.rag.retriever import search_policy


def test_documents_exist():
    """Verify that sample policy PDFs exist in data/documents."""
    doc_dir = Path("data/documents")
    assert doc_dir.exists(), "data/documents directory must exist."
    pdfs = list(doc_dir.glob("*.pdf"))
    assert len(pdfs) >= 10, f"Expected at least 10 policy PDFs, found {len(pdfs)}."


def test_load_single_pdf():
    """Verify loading text and metadata from a specific PDF."""
    pdf_path = Path("data/documents/leave_policy.pdf")
    if not pdf_path.exists():
        pytest.skip("leave_policy.pdf not generated yet.")

    pages = load_single_pdf(pdf_path)
    assert len(pages) > 0
    assert pages[0]["source"] == "leave_policy.pdf"
    assert pages[0]["department"] == "Human Resources"
    assert pages[0]["page"] == 1
    assert len(pages[0]["text"]) > 20


def test_load_all_documents():
    """Verify loading all policy PDFs from data/documents."""
    all_pages = load_all_documents("data/documents")
    assert len(all_pages) >= 10
    sources = set(p["source"] for p in all_pages)
    assert "leave_policy.pdf" in sources
    assert "wfh_policy.pdf" in sources


def test_chunk_documents():
    """Verify chunking creates chunks with proper metadata and chunk_id."""
    sample_pages = [
        {
            "text": "TechNova Casual Leave rules. Employees are entitled to 12 casual leaves per year. Maximum 3 consecutive casual leaves are allowed.",
            "source": "leave_policy.pdf",
            "page": 2,
            "department": "HR",
            "policy_version": "2.1",
            "document_type": "Leave Policy"
        }
    ]
    chunks = chunk_documents(sample_pages, chunk_size=200, chunk_overlap=50)
    assert len(chunks) > 0
    chunk = chunks[0]
    assert "chunk_id" in chunk
    assert chunk["source"] == "leave_policy.pdf"
    assert chunk["page"] == 2
    assert chunk["department"] == "HR"
    assert "12 casual leaves" in chunk["text"]


def test_faiss_vectorstore_and_retrieval():
    """Verify FAISS vectorstore loads and returns grounded results with source and page."""
    store = load_vectorstore("data/vectorstore")
    if not store:
        pytest.skip("FAISS vectorstore not yet indexed. Run python -m app.rag.index first.")

    index, metadata = store
    assert index.ntotal > 0
    assert len(metadata) == index.ntotal

    # Search for casual leave
    results = search_policy("How many casual leaves are allowed?", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert "text" in top
    assert "source" in top
    assert "page" in top
    assert "score" in top
    assert top["source"].endswith(".pdf")
    assert isinstance(top["page"], int)
