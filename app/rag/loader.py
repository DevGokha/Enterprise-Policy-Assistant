"""PDF Document loader for Enterprise Policy documents."""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader

logger = logging.getLogger(__name__)

DOC_REGISTRY = {
    "leave_policy.pdf": {
        "department": "Human Resources",
        "policy_version": "2.1",
        "document_type": "Leave Policy"
    },
    "wfh_policy.pdf": {
        "department": "Operations & HR",
        "policy_version": "3.0",
        "document_type": "Hybrid & Remote Work Policy"
    },
    "attendance_policy.pdf": {
        "department": "Human Resources",
        "policy_version": "1.8",
        "document_type": "Attendance Policy"
    },
    "travel_policy.pdf": {
        "department": "Finance & Administration",
        "policy_version": "2.4",
        "document_type": "Travel Policy"
    },
    "reimbursement_policy.pdf": {
        "department": "Finance & Accounts",
        "policy_version": "2.0",
        "document_type": "Reimbursement Policy"
    },
    "employee_benefits.pdf": {
        "department": "Total Rewards & HR",
        "policy_version": "3.2",
        "document_type": "Employee Benefits Policy"
    },
    "code_of_conduct.pdf": {
        "department": "Legal & Compliance",
        "policy_version": "4.0",
        "document_type": "Code of Conduct"
    },
    "information_security_policy.pdf": {
        "department": "Information Security",
        "policy_version": "2.2",
        "document_type": "Information Security Policy"
    },
    "holiday_policy.pdf": {
        "department": "Human Resources",
        "policy_version": "2.0",
        "document_type": "Holiday Policy"
    },
    "hr_handbook.pdf": {
        "department": "Human Resources",
        "policy_version": "5.0",
        "document_type": "HR Handbook"
    }
}


def load_single_pdf(file_path: Path) -> List[Dict[str, Any]]:
    """Extract page-level text and metadata from a single PDF document.
    
    Args:
        file_path: Path to the PDF file.
        
    Returns:
        List of dictionaries containing page text, source filename, page number, and metadata.
    """
    filename = file_path.name
    doc_info = DOC_REGISTRY.get(filename, {
        "department": "General",
        "policy_version": "1.0",
        "document_type": filename.replace("_", " ").replace(".pdf", "").title()
    })

    pages_data = []
    try:
        reader = PdfReader(str(file_path))
        num_pages = len(reader.pages)
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            # Clean trailing whitespace
            cleaned_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
            if cleaned_text:
                pages_data.append({
                    "text": cleaned_text,
                    "source": filename,
                    "page": idx + 1,
                    "total_pages": num_pages,
                    "department": doc_info["department"],
                    "policy_version": doc_info["policy_version"],
                    "document_type": doc_info["document_type"]
                })
        logger.info(f"Loaded {len(pages_data)} pages from {filename}")
    except Exception as e:
        logger.error(f"Error loading PDF {file_path}: {e}")
        raise

    return pages_data


def load_all_documents(docs_dir: str = "data/documents") -> List[Dict[str, Any]]:
    """Load all PDF documents from the documents directory.
    
    Args:
        docs_dir: Directory containing policy PDFs.
        
    Returns:
        List of all extracted page-level data.
    """
    directory = Path(docs_dir)
    if not directory.exists():
        logger.warning(f"Documents directory {docs_dir} does not exist.")
        return []

    pdf_files = sorted(list(directory.glob("*.pdf")))
    logger.info(f"Found {len(pdf_files)} PDF files in {docs_dir}")

    all_pages = []
    for pdf_path in pdf_files:
        pages = load_single_pdf(pdf_path)
        all_pages.extend(pages)

    logger.info(f"Successfully loaded a total of {len(all_pages)} pages from {len(pdf_files)} documents.")
    return all_pages
