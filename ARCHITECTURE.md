# Architecture & Technical Design — Enterprise Policy Assistant

This document outlines the architectural blueprint, data flows, and design decisions for the **TechNova Enterprise Policy Assistant**. This reference is designed for technical deep-dives and engineering interviews (e.g., TCS NQT / AI-ML / GenAI Specialist interviews).

---

## 1. High-Level System Architecture

The Enterprise Policy Assistant combines **Retrieval-Augmented Generation (RAG)** for company knowledge retrieval with a **controlled Agentic AI workflow (LangGraph)** for deterministic, stateful HR actions.

```mermaid
graph TD
    User([👤 TechNova Employee]) -->|HTTP / WebSocket| UI[🖥️ Streamlit Web Dashboard]
    UI -->|REST JSON API| API[⚡ FastAPI Application Gateway]
    
    subgraph Core AI & Workflow Engine
        API --> Router[🧭 LangGraph Agent State Router]
        
        Router -->|Intent: policy_question| RAG[🔍 RAG Knowledge Pipeline]
        Router -->|Intent: leave_balance| Tool_Bal[📊 Leave Balance Tool]
        Router -->|Intent: leave_status| Tool_Stat[🔎 Request Status Tool]
        Router -->|Intent: employee_info| Tool_Emp[👤 Employee Profile Tool]
        Router -->|Intent: leave_request| AgenticFlow[🛡️ Guarded Leave Workflow]
    end

    subgraph RAG Knowledge Pipeline
        RAG --> Embed[🧠 SentenceTransformer all-MiniLM-L6-v2]
        Embed --> FAISS[(🗄️ FAISS Vector Index)]
        FAISS --> TopK[📄 Top-K Context Chunks + Page Citations]
        TopK --> LLM[🤖 Groq LLM llama-3.3-70b-versatile]
    end

    subgraph HR Tools & State Management
        AgenticFlow --> Step1[1. Check Employee Profile]
        Step1 --> Step2[2. Calculate Working Days]
        Step2 --> Step3[3. Check Leave Balance & Eligibility]
        Step3 --> Step4{4. Confirmed by User?}
        Step4 -->|No| AskConf[Ask Confirmation & Lock Action]
        Step4 -->|Yes| ExecReq[Execute Transaction & Deduct Balance]
    end

    subgraph Persistence Layer
        Tool_Bal --> DB[(💾 SQLite Database enterprise.db)]
        Tool_Stat --> DB
        Tool_Emp --> DB
        ExecReq --> DB
    end

    RAG --> RespGen[Structured Response Generator]
    AgenticFlow --> RespGen
    Tool_Bal --> RespGen
    RespGen -->|Answer + Citations + Actions| API
    API --> UI
```

---

## 2. Core Conceptual Distinction (Interview Essentials)

In modern Generative AI engineering, a common question is distinguishing between **RAG**, **GenAI**, and **Agentic AI**. This project demonstrates all three in harmony:

| Concept | Core Responsibility | Implementation in TechNova Assistant |
| :--- | :--- | :--- |
| **RAG** (Retrieval-Augmented Generation) | **Retrieves external domain knowledge** that the model was never trained on, preventing factual hallucination. | Extracts, chunks, embeds 10 TechNova policy PDFs into FAISS; retrieves exact policy snippets with document and page numbers. |
| **GenAI** (Generative AI) | **Synthesizes natural-language answers** grounded in provided context. | Synthesizes professional, readable answers grounded strictly on retrieved policy excerpts via Groq API. |
| **Agentic AI** | **Autonomously reasons, plans, and selects tools** to accomplish multi-step goals with stateful execution. | The LangGraph state machine determines intent, checks employee eligibility, calculates working days, demands confirmation, and updates SQLite. |

---

## 3. End-to-End User Interaction Flows

### Flow A: Knowledge Policy Request (RAG)
Example: *"How many casual leaves are allowed?"*

```mermaid
sequenceDiagram
    autonumber
    actor Employee as 👤 Employee
    participant UI as 🖥️ Streamlit UI
    participant API as ⚡ FastAPI (/api/chat)
    participant Agent as 🧭 LangGraph Agent
    participant Retriever as 🔍 FAISS Retriever
    participant LLM as 🤖 Groq LLM
    
    Employee->>UI: "How many casual leaves are allowed?"
    UI->>API: POST /api/chat {employee_id: "EMP001", message: "..."}
    API->>Agent: invoke(AgentState)
    Agent->>Agent: classify_intent_node() -> 'policy_question'
    Agent->>Retriever: search_policy("casual leaves allowed", top_k=5)
    Retriever-->>Agent: Returns 5 chunks [leave_policy.pdf, Page 2 & 3]
    Agent->>LLM: generate_rag_answer(context, question)
    Note over LLM: Grounded strictly on retrieved policy context.<br/>Includes source document and page citation.
    LLM-->>Agent: "Employees are entitled to 12 casual leaves per year..."
    Agent-->>API: {answer, intent: "policy_question", sources: [...]}
    API-->>UI: 200 OK
    UI-->>Employee: Displays grounded answer with 📄 leave_policy.pdf, Page 2
```

### Flow B: HR Action Request with Confirmation Safety (Agentic AI)
Example: *"Apply casual leave from October 5 to October 7."*

```mermaid
sequenceDiagram
    autonumber
    actor Employee as 👤 Employee
    participant UI as 🖥️ Streamlit UI
    participant API as ⚡ FastAPI
    participant Agent as 🧭 LangGraph Agent
    participant DB as 💾 SQLite (enterprise.db)
    
    Employee->>UI: "Apply casual leave from October 5 to October 7"
    UI->>API: POST /api/chat {confirmed: false}
    API->>Agent: invoke(AgentState)
    Agent->>Agent: classify_intent_node() -> 'leave_request'
    Agent->>DB: get_employee("EMP001") -> Dev Kumar (AI/ML)
    Agent->>Agent: calculate_leave_days("2026-10-05", "2026-10-07") -> 3 working days
    Agent->>DB: get_leave_balance("EMP001", "casual_leave") -> 8 days
    Agent->>Agent: check_leave_eligibility() -> Eligible (8 >= 3)
    Note over Agent: CONFIRMATION GUARDRAIL TRIGGERED:<br/>State change blocked until explicit user confirmation.
    Agent-->>API: {confirmation_required: true, requested_days: 3, balance: 8}
    API-->>UI: Renders interactive "[Confirm Leave Request]" button
    
    opt Confirmation Step
        Employee->>UI: Clicks "[Confirm Leave Request]"
        UI->>API: POST /api/chat {confirmed: true}
        API->>Agent: invoke(AgentState with confirmed=True)
        Agent->>DB: BEGIN TRANSACTION
        Agent->>DB: Deduct 3 casual leaves from balance (8 -> 5)
        Agent->>DB: INSERT into leave_requests -> "LV1025" (Pending)
        Agent->>DB: COMMIT TRANSACTION
        Agent-->>API: "Leave request submitted successfully. Request ID: LV1025"
        API-->>UI: Updates UI & displays Request ID: LV1025
    end
```

---

## 4. Database Schema (Entity Relationship Diagram)

```mermaid
erDiagram
    EMPLOYEES ||--|| LEAVE_BALANCE : "has"
    EMPLOYEES ||--o{ LEAVE_REQUESTS : "submits"

    EMPLOYEES {
        string employee_id PK "EMP001, EMP002..."
        string name "Full Name"
        string email "Unique Corporate Email"
        string department "Engineering, HR, etc."
        string manager "Reporting Manager"
    }

    LEAVE_BALANCE {
        string employee_id PK, FK "References EMPLOYEES"
        int casual_leave "Annual Casual Leaves"
        int sick_leave "Annual Sick Leaves"
        int paid_leave "Accumulated Privilege Leaves"
    }

    LEAVE_REQUESTS {
        string request_id PK "Unique identifier e.g. LV1025"
        string employee_id FK "References EMPLOYEES"
        string start_date "YYYY-MM-DD"
        string end_date "YYYY-MM-DD"
        string leave_type "casual_leave / sick_leave / paid_leave"
        int days "Working days count"
        string status "Pending / Approved / Rejected"
        datetime created_at "Submission timestamp"
    }
```

---

## 5. Security Guardrails & Enterprise Governance

1. **Strict Context Grounding**: The LLM system prompt forbids answering ungrounded queries. If documents lack the answer, the system replies: *"I could not find this information in the available company policy documents."*
2. **Deterministic State Changes**: State-changing database mutations (leave creation, balance deduction) are physically decoupled from direct LLM output. The LLM only classifies intent; Python code executes validated database transactions.
3. **Negative Balance Prevention**: The `check_leave_eligibility` and `create_leave_request` tools enforce that requested days strictly do not exceed current balances.
4. **Calendar Validation**: Automatically discounts weekends (Saturdays and Sundays) and verifies that `start_date <= end_date`.
5. **No Arbitrary SQL**: All database operations use SQLAlchemy ORM parameterization, completely eliminating SQL injection vectors.
6. **Zero Leaked Credentials**: Secret keys are loaded solely through environment variables (`.env`).
