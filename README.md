# 🏢 Roboserv 4i Enterprise Policy Assistant

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Single--Agent-FF6F00?style=flat)](https://github.com/langchain-ai/langgraph)
[![FAISS](https://img.shields.io/badge/FAISS-VectorStore-00599C?style=flat)](https://github.com/facebookresearch/faiss)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, portfolio-ready AI Employee Assistant built for **Roboserv 4i Private Limited** that combines **Retrieval-Augmented Generation (RAG)** for policy knowledge questions with an **Agentic AI workflow (LangGraph)** for automated HR tasks with **human-in-the-loop confirmation safety**.

Designed specifically for **TCS NQT / AI-ML / GenAI Specialist interview portfolios**, showcasing clean software design, production guardrails, and real retrieval without mockups.

---

## 📑 Table of Contents
- [1. Business Problem & Solution](#1-business-problem--solution)
- [2. Key Features](#2-key-features)
- [3. Architecture Overview](#3-architecture-overview)
- [4. RAG vs GenAI vs Agentic AI](#4-rag-vs-genai-vs-agentic-ai)
- [5. Technology Stack](#5-technology-stack)
- [6. Project Directory Structure](#6-project-directory-structure)
- [7. Installation & Setup](#7-installation--setup)
- [8. Execution Commands](#8-execution-commands)
- [9. Demo Scenarios & User Flows](#9-demo-scenarios--user-flows)
- [10. API Specification & Examples](#10-api-specification--examples)
- [11. Confirmation Safety & Security Guardrails](#11-confirmation-safety--security-guardrails)
- [12. Future Roadmap & Scaling](#12-future-roadmap--scaling)

---

## 1. Business Problem & Solution

### The Business Challenge
In modern enterprises, HR departments receive thousands of repetitive inquiries every week concerning leave balances, work-from-home rules, travel allowances, medical insurance, and notice periods. Employees often struggle to locate exact policy rules in dense PDF documents, while manual leave verification drains HR productivity.

### The Solution
The **Enterprise Policy Assistant** provides:
1. **Instant, Grounded Answers**: Pulls exact clauses from 10 official Roboserv 4i policy documents and cites the **document name and page number**.
2. **Zero Hallucination Guarantee**: Strictly declines to answer if the clause does not exist in company records.
3. **Agentic Action Execution**: Resolves leave balances, computes working days (excluding weekends), and checks balance eligibility.
4. **State-Change Confirmation Safety**: Prevents unauthorized balance deductions by enforcing explicit user approval before touching SQLite.

---

## 2. Key Features

- 🔍 **Real RAG Pipeline**: Extracts, chunks, and indexes 10 authentic Roboserv 4i policy PDFs using `sentence-transformers/all-MiniLM-L6-v2` and FAISS.
- 📄 **Precise Citations**: Every policy response displays the source document and page number (e.g. `leave_policy.pdf, Page 3`).
- 🤖 **Single-Agent LangGraph Workflow**: Controlled state machine that routes queries between knowledge retrieval and HR action tools without unnecessary multi-agent complexity.
- 🛡️ **Confirmation Guardrails**: State-changing operations (such as submitting leave requests and deducting leave balances) require explicit user confirmation.
- 💾 **Relational SQLite Storage**: Clean SQLAlchemy models storing employees, leave balances, and request histories.
- 🌐 **Full-Stack REST & UI**: Robust FastAPI backend with CORS + interactive Streamlit dashboard.

---

## 3. Architecture Overview

```
User (Employee)
       ↓
  Streamlit UI (Port 8501)
       ↓
  FastAPI Backend (Port 8000)
       ↓
  LangGraph Agent Router
       ├── [Intent: policy_question] ────────→ RAG Pipeline
       │                                        ├── Chunking & Metadata
       │                                        ├── SentenceTransformers (all-MiniLM-L6-v2)
       │                                        ├── FAISS Vector Index
       │                                        └── Groq LLM (llama-3.3-70b-versatile)
       │
       └── [Intent: leave_request / balance] ──→ HR Tools Layer
                                                ├── Employee Lookup Tool
                                                ├── Working-Day Calculation Tool
                                                ├── Leave Eligibility Tool
                                                └── Leave Request Tool (Transactional)
                                                        ↓
                                                SQLite (enterprise.db)
```

---

## 4. RAG vs GenAI vs Agentic AI

| Paradigm | What it does | Role in this Project |
| :--- | :--- | :--- |
| **RAG** | *Retrieves knowledge* | Discovers relevant clauses from 10 company policy PDFs with page numbers. |
| **GenAI** | *Generates language* | Turns retrieved excerpts into natural, professional explanations. |
| **Agentic AI** | *Decides & takes action* | Evaluates employee state, checks leave balances, asks confirmation, and writes to the database. |

---

## 5. Technology Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2
- **Agent Orchestration**: LangGraph, LangChain Core
- **RAG & Embeddings**: FAISS (`faiss-cpu`), `sentence-transformers` (`all-MiniLM-L6-v2`), PyPDF
- **LLM Provider**: Groq API (`llama-3.3-70b-versatile`) with offline fallback
- **Database**: SQLite, SQLAlchemy ORM
- **Frontend**: Streamlit
- **Testing**: Pytest, HTTPX

---

## 6. Project Directory Structure

```
enterprise-policy-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application & lifecycle
│   │
│   ├── agent/                      # LangGraph Agentic AI package
│   │   ├── __init__.py
│   │   ├── graph.py                # StateGraph workflow definition & routing
│   │   ├── state.py                # TypedDict & Pydantic AgentState schemas
│   │   ├── nodes.py                # Workflow nodes & business logic
│   │   ├── prompts.py              # Strict system prompts & citation instructions
│   │   └── llm.py                  # Groq API client with resilient fallbacks
│   │
│   ├── rag/                        # RAG Pipeline package
│   │   ├── __init__.py
│   │   ├── loader.py               # PyPDF text & metadata extraction
│   │   ├── chunker.py              # Semantic text chunker with ID tracking
│   │   ├── embeddings.py           # SentenceTransformer embedding service
│   │   ├── vectorstore.py          # FAISS index persistence & search
│   │   ├── retriever.py            # Search policy function
│   │   └── index.py                # Document indexing script (CLI runner)
│   │
│   ├── tools/                      # Reusable tool modules
│   │   ├── __init__.py
│   │   ├── policy_tool.py          # search_policy()
│   │   ├── employee_tool.py        # get_employee()
│   │   ├── leave_tool.py           # get_leave_balance(), calculate_days(), check_eligibility()
│   │   └── request_tool.py         # create_leave_request(), get_status()
│   │
│   ├── database/                   # SQLite + SQLAlchemy layer
│   │   ├── __init__.py
│   │   ├── database.py             # Engine & SessionLocal setup
│   │   ├── models.py               # Employee, LeaveBalance, LeaveRequest ORM
│   │   └── seed.py                 # Sample employee seeding script
│   │
│   └── api/                        # REST API routers
│       ├── __init__.py
│       └── chat.py                 # /api/chat, /api/leave/* endpoints
│
├── data/
│   ├── documents/                  # 10 official Roboserv 4i policy PDFs
│   ├── vectorstore/                # Generated FAISS index & metadata
│   ├── enterprise.db               # SQLite database
│   └── generate_documents.py       # Programmatic PDF generation script
│
├── tests/
│   ├── test_rag.py                 # Loader, chunking, retrieval tests
│   ├── test_agent.py               # Intent routing & confirmation safety tests
│   └── test_tools.py               # Employee, balance, calculation, eligibility tests
│
├── streamlit_app.py                # Streamlit enterprise web dashboard
├── requirements.txt                # Production dependencies
├── .env.example                    # Environment template
├── Dockerfile                      # Container build definition
├── README.md                       # Comprehensive guide & interview prep
└── ARCHITECTURE.md                 # Deep-dive architecture & Mermaid diagrams
```

---

## 7. Installation & Setup

### Prerequisites
- Python 3.10 or 3.11+
- Virtual environment (`venv`)

### 1. Clone & create virtual environment
```bash
git clone https://github.com/yourusername/Enterprise-Policy-Assistant.git
cd Enterprise-Policy-Assistant

python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and insert your Groq API key:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
DATABASE_URL=sqlite:///data/enterprise.db
VECTORSTORE_DIR=data/vectorstore
DOCUMENTS_DIR=data/documents
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

---

## 8. Execution Commands

### Step 1: Generate Policy PDFs
Generate 10 official fictional policy documents for Roboserv 4i:
```bash
python -m data.generate_documents
```

### Step 2: Seed SQLite Database
Seed sample employees (`EMP001` to `EMP005`) and starting leave balances:
```bash
python -m app.database.seed
```

### Step 3: Index Documents into FAISS
Extract, chunk, embed, and build the FAISS index:
```bash
python -m app.rag.index
```

### Step 4: Run the FastAPI Backend
```bash
uvicorn app.main:app --reload --port 8000
```
Swagger UI will be accessible at: `http://localhost:8000/docs`

### Step 5: Run the Streamlit Dashboard
In a new terminal window (with `.venv` active):
```bash
streamlit run streamlit_app.py
```
The dashboard will open automatically at: `http://localhost:8501`

### Step 6: Run Unit & Integration Tests
```bash
pytest -v
```

---

## 9. Demo Scenarios & User Flows

### Scenario 1 — Policy Question (RAG)
- **User Input:** *"How many casual leaves are allowed?"*
- **Assistant Response:**
  > "According to the Leave Policy, employees are entitled to 12 casual leaves per year. Casual leaves cannot be taken for more than 3 consecutive working days without prior managerial approval."
- **Source Citation:** `📄 leave_policy.pdf, Page 2`

### Scenario 2 — Leave Balance (Database Tool)
- **User Input:** *"How many paid leaves do I have?"*
- **Assistant Response:**
  > "Dev Kumar (EMP001), you currently have **15 days** of Paid Leave remaining."
- **Action Status:** `⚡ Action: check_leave_balance (completed)`

### Scenario 3 — Agentic Leave Request (Confirmation Safety)
- **User Input:** *"Apply casual leave from October 5 to October 7."*
- **Assistant Response:**
  > "You are requesting **3 working day(s)** of casual leave from **2026-10-05** to **2026-10-07**.\n\n• Current Leave Balance: 8 days\n• Requested Duration: 3 days\n• Remaining Balance After Approval: 5 days\n• Status: Eligible\n\nWould you like me to submit this leave request?"
- **UI Element:** Renders interactive `[Confirm Leave Request]` button.
- **User Action:** Clicks `[Confirm Leave Request]` or types *"Yes, submit it."*
- **Assistant Response:**
  > "Leave request submitted successfully.\n\n• **Request ID:** **LV1025**\n• **Employee:** Dev Kumar (EMP001)\n• **Period:** 2026-10-05 to 2026-10-07 (3 working day(s))\n• **Leave Type:** Casual Leave\n• **Updated Balance:** 5 days\n• **Status:** Pending approval by your manager (Rahul Sharma)."

---

## 10. API Specification & Examples

### 1. Send Chat Message (`POST /api/chat`)
```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "employee_id": "EMP001",
       "message": "What is the work from home policy?"
     }'
```
**Response:**
```json
{
  "answer": "According to the Hybrid & Remote Work Policy, regular full-time employees may work from home for up to 2 days per week with manager approval. Core working hours are 10:00 AM to 5:00 PM IST.",
  "intent": "policy_question",
  "sources": [
    {
      "document": "wfh_policy.pdf",
      "page": 1,
      "department": "Operations & HR"
    }
  ],
  "actions": [],
  "confirmation_required": false
}
```

### 2. Check Employee Profile (`GET /api/employee/{id}`)
```bash
curl "http://localhost:8000/api/employee/EMP001"
```

### 3. Check Leave Balance (`GET /api/employee/{id}/leave-balance`)
```bash
curl "http://localhost:8000/api/employee/EMP001/leave-balance"
```

### 4. Trigger Vector Indexing (`POST /api/index`)
```bash
curl -X POST "http://localhost:8000/api/index"
```

---

## 11. Confirmation Safety & Security Guardrails

1. **Human-in-the-Loop Confirmation**: The assistant will **never** mutate database balances upon initial request. It validates the policy rules, verifies remaining balance, calculates calendar workdays, and awaits user confirmation.
2. **Zero Policy Hallucination**: If the query is outside company policies, the LLM is instructed: *"I could not find this information in the available company policy documents."*
3. **No Arbitrary SQL Execution**: The agent never generates SQL queries. All interactions use pre-defined, typed SQLAlchemy ORM queries with parameterized sanitization.
4. **Preventing Negative Balances**: Leave eligibility checks fail deterministically if `requested_days > balance` or if `days <= 0`.
5. **Weekend Deductions**: Automatically discounts non-working weekend days (Saturdays and Sundays).

---

## 12. Future Roadmap & Scaling
- [ ] Add Multi-factor Approval Matrix (Manager notification via Slack / Teams webhook)
- [ ] Implement Hybrid Search (BM25 lexical search + FAISS dense semantic search)
- [ ] Add PDF Viewer in Streamlit with highlighted source clauses
- [ ] Expand to multi-lingual policy translation for international employees

---

**Developed with ❤️ for Roboserv 4i Private Limited**
