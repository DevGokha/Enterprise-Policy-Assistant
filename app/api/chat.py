"""FastAPI router for Chat and Enterprise Assistant endpoints."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.agent.graph import run_agent_workflow
from app.rag.index import run_indexing
from app.tools.employee_tool import get_employee
from app.tools.leave_tool import get_leave_balance, calculate_leave_days, check_leave_eligibility
from app.tools.request_tool import create_leave_request, get_leave_request_status, get_employee_leave_requests
from app.database.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Assistant & HR"])


# ---------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------

class ChatRequest(BaseModel):
    employee_id: str = Field(default="EMP001", description="Employee ID")
    message: str = Field(..., description="User query or message")
    confirmed: bool = Field(default=False, description="Explicit confirmation flag for leave submission")
    extra_state: Optional[Dict[str, Any]] = Field(default=None, description="Optional previous conversation state")


class SourceItem(BaseModel):
    document: str
    page: int
    department: Optional[str] = None
    document_type: Optional[str] = None


class ActionItem(BaseModel):
    action: str
    status: str
    details: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    confirmation_required: bool = False
    confirmed: bool = False
    request_id: Optional[str] = None
    error: Optional[str] = None


class CalculateLeaveRequest(BaseModel):
    start_date: str = Field(..., description="Start date (e.g. '2026-10-05')")
    end_date: str = Field(..., description="End date (e.g. '2026-10-07')")


class CheckEligibilityRequest(BaseModel):
    employee_id: str = Field(..., description="Employee ID (e.g. 'EMP001')")
    leave_type: str = Field(..., description="Leave type: casual_leave, sick_leave, paid_leave")
    days: int = Field(..., description="Number of working days")


class SubmitLeaveRequest(BaseModel):
    employee_id: str
    start_date: str
    end_date: str
    leave_type: str
    days: int
    confirm: bool = Field(default=False, description="Safety confirmation flag")


class AgentWorkflowRequest(BaseModel):
    query: str
    employee_id: str = "EMP001"
    confirmed: bool = False
    extra_state: Optional[Dict[str, Any]] = None


class TranslateRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target_lang: str = Field(default="hi", description="Target language code: 'hi' (Hindi), 'mr' (Marathi), 'en' (English)")


class TranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    target_lang: str


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """Main conversational endpoint for the Enterprise Policy Assistant.
    Routes queries to RAG retriever, leave balance tool, or agentic leave workflow.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        from app.agent.llm import translate_to_english, translate_text
        query = req.message
        has_devanagari = any('\u0900' <= char <= '\u097f' for char in query)
        if has_devanagari:
            query = translate_to_english(query)
            logger.info(f"Translated query for agent: '{query}'")

        result = run_agent_workflow(
            query=query,
            employee_id=req.employee_id,
            confirmed=req.confirmed,
            extra_state=req.extra_state
        )

        final_ans = result.get("final_response", "")
        if has_devanagari and final_ans:
            final_ans = translate_text(final_ans, "hi")

        return ChatResponse(
            answer=final_ans,
            intent=result.get("intent", "general_question"),
            sources=result.get("sources", []),
            actions=result.get("actions", []),
            confirmation_required=result.get("confirmation_required", False),
            confirmed=result.get("confirmed", False),
            request_id=result.get("request_id"),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Error executing chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal assistant error: {str(e)}")


@router.post("/translate", response_model=TranslateResponse)
def translate_endpoint(req: TranslateRequest):
    """Translate assistant response to Hindi or Marathi."""
    if not req.text.strip():
        return TranslateResponse(original_text="", translated_text="", target_lang=req.target_lang)
    from app.agent.llm import translate_text
    try:
        translated = translate_text(req.text, req.target_lang)
        return TranslateResponse(
            original_text=req.text,
            translated_text=translated,
            target_lang=req.target_lang
        )
    except Exception as e:
        logger.error(f"Translation endpoint error: {e}")
        return TranslateResponse(
            original_text=req.text,
            translated_text=req.text,
            target_lang=req.target_lang
        )


@router.post("/agent")
def agent_endpoint(req: AgentWorkflowRequest):
    """Directly invoke the LangGraph Agent workflow."""
    try:
        result = run_agent_workflow(
            query=req.query,
            employee_id=req.employee_id,
            confirmed=req.confirmed,
            extra_state=req.extra_state
        )
        return {
            "status": "success",
            "state": result
        }
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
def index_documents_endpoint():
    """Trigger PDF extraction, chunking, embedding, and FAISS indexing."""
    try:
        count = run_indexing()
        return {
            "status": "success",
            "message": f"Successfully indexed {count} policy vectors into FAISS."
        }
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.get("/employee/{employee_id}")
def get_employee_endpoint(employee_id: str):
    """Fetch employee profile information."""
    emp = get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")
    return emp


@router.get("/employee/{employee_id}/leave-balance")
def get_leave_balance_endpoint(employee_id: str):
    """Fetch all leave balances for the given employee."""
    bal = get_leave_balance(employee_id)
    if "error" in bal:
        raise HTTPException(status_code=404, detail=bal["error"])
    return bal


@router.get("/employee/{employee_id}/leave-requests")
def get_employee_leave_requests_endpoint(employee_id: str):
    """Fetch recent leave requests for the given employee."""
    reqs = get_employee_leave_requests(employee_id)
    return reqs



@router.post("/leave/calculate")
def calculate_leave_endpoint(req: CalculateLeaveRequest):
    """Calculate working days between two dates, excluding weekends."""
    calc = calculate_leave_days(req.start_date, req.end_date)
    if not calc["valid"]:
        raise HTTPException(status_code=400, detail=calc["error"])
    return calc


@router.post("/leave/check")
def check_leave_eligibility_endpoint(req: CheckEligibilityRequest):
    """Verify if the employee has sufficient balance and complies with policies."""
    elig = check_leave_eligibility(req.employee_id, req.leave_type, req.days)
    return elig


@router.post("/leave/request")
def submit_leave_request_endpoint(req: SubmitLeaveRequest):
    """Submit a leave request. Requires safety confirmation flag."""
    if not req.confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Set 'confirm=true' after user explicitly validates the request."
        )

    res = create_leave_request(
        employee_id=req.employee_id,
        start_date=req.start_date,
        end_date=req.end_date,
        leave_type=req.leave_type,
        days=req.days
    )
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.get("/leave/request/{request_id}")
def get_leave_request_endpoint(request_id: str):
    """Get leave request status by request ID."""
    req_data = get_leave_request_status(request_id)
    if not req_data:
        raise HTTPException(status_code=404, detail=f"Leave request '{request_id}' not found.")
    return req_data


@router.get("/documents/{filename}")
def get_document_pdf(filename: str):
    """Serve policy PDF document by filename."""
    # Prevent directory traversal attacks
    clean_filename = Path(filename).name
    doc_path = Path("data/documents") / clean_filename
    if not doc_path.exists() or not doc_path.is_file():
        raise HTTPException(status_code=404, detail=f"Policy document '{clean_filename}' not found.")
    return FileResponse(
        path=str(doc_path),
        filename=clean_filename,
        media_type="application/pdf"
    )
