"""Typed agent state definition for the LangGraph workflow."""

from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AgentState(TypedDict, total=False):
    """LangGraph workflow state schema."""
    user_query: str
    employee_id: str
    intent: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    leave_type: Optional[str]
    requested_days: Optional[int]
    leave_balance: Optional[Dict[str, Any]]
    eligibility: Optional[Dict[str, Any]]
    confirmation_required: bool
    confirmed: bool
    request_id: Optional[str]
    retrieved_context: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    final_response: str
    error: Optional[str]


class AgentStateModel(BaseModel):
    """Pydantic model representation of AgentState for API serialization."""
    user_query: str
    employee_id: str = "EMP001"
    intent: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    leave_type: Optional[str] = None
    requested_days: Optional[int] = None
    leave_balance: Optional[Dict[str, Any]] = None
    eligibility: Optional[Dict[str, Any]] = None
    confirmation_required: bool = False
    confirmed: bool = False
    request_id: Optional[str] = None
    retrieved_context: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    final_response: str = ""
    error: Optional[str] = None
