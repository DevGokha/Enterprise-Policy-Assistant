"""Workflow nodes for the LangGraph Enterprise Policy Assistant."""

import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from app.agent.state import AgentState
from app.agent.llm import generate_rag_answer, get_llm
from app.agent.prompts import ROUTER_SYSTEM_PROMPT
from app.tools.policy_tool import search_policy
from app.tools.employee_tool import get_employee
from app.tools.leave_tool import (
    get_leave_balance,
    calculate_leave_days,
    check_leave_eligibility,
    normalize_leave_type
)
from app.tools.request_tool import create_leave_request, get_leave_request_status

logger = logging.getLogger(__name__)


def extract_dates_from_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract start_date and end_date from text using patterns like:
    - 'from October 5 to October 7'
    - 'from 2026-10-05 to 2026-10-07'
    - 'from 5 Oct to 7 Oct'
    - 'from Oct 5th to Oct 7th'
    """
    clean_q = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', query)
    current_year = datetime.now().year

    # Pattern: from <date1> to <date2> or between <date1> and <date2>
    patterns = [
        r'(?:from|between)\s+([A-Za-z0-9\-\/,\s]+?)\s+(?:to|and|-)\s+([A-Za-z0-9\-\/,\s]+?)(?:\.|$|\s+for|\s+due|\s+as)',
        r'(\d{4}-\d{2}-\d{2})\s+(?:to|-)\s+(\d{4}-\d{2}-\d{2})',
        r'([A-Za-z]+\s+\d{1,2})\s+(?:to|-)\s+([A-Za-z]+\s+\d{1,2})',
        r'([A-Za-z]+\s+\d{1,2})\s+(?:to|-)\s+(\d{1,2})'  # e.g., "October 5 to 7"
    ]

    for pat in patterns:
        m = re.search(pat, clean_q, re.IGNORECASE)
        if m:
            s_raw, e_raw = m.group(1).strip(), m.group(2).strip()
            # If e_raw is just day digits like "7" in "October 5 to 7", prepend month
            if e_raw.isdigit():
                month_match = re.search(r'([A-Za-z]+)', s_raw)
                if month_match:
                    e_raw = f"{month_match.group(1)} {e_raw}"
            return s_raw, e_raw

    # Single date pattern: 'on October 5' or 'for October 5'
    single_match = re.search(r'(?:on|for)\s+([A-Za-z]+\s+\d{1,2}(?:,\s*\d{4})?|\d{4}-\d{2}-\d{2})', clean_q, re.IGNORECASE)
    if single_match:
        d = single_match.group(1).strip()
        return d, d

    return None, None


def classify_intent_rule_based(query: str) -> Dict[str, Any]:
    """Fast, deterministic intent classifier and parameter extractor."""
    q_lower = query.lower().strip()

    # 1. Confirmation check
    confirm_words = ["yes", "confirm", "submit it", "yes, submit", "please submit", "proceed", "go ahead", "approved", "confirm leave request"]
    is_confirm = any(w == q_lower or q_lower.startswith(w) for w in confirm_words)

    # 2. Leave Request check
    request_keywords = ["apply leave", "apply for leave", "request leave", "take leave", "take casual leave", "take sick leave", "take paid leave", "apply casual", "apply sick", "apply paid", "book leave"]
    is_leave_request = any(kw in q_lower for kw in request_keywords) or (("apply" in q_lower or "request" in q_lower) and "leave" in q_lower)

    # 3. Policy question indicators
    policy_indicators = ["allowed", "entitled", "policy", "rules", "rule", "per year", "annual", "eligible for", "guideline", "maximum", "max", "carry forward", "encashment"]
    has_policy_indicator = any(p in q_lower for p in policy_indicators)

    # 4. Leave Balance check (Personal balance: "do i have", "my leaves", "my balance", "remaining", "for me")
    personal_indicators = ["do i have", "my leave", "my balance", "remaining", "for me", "left", "have i got", "my casual", "my sick", "my paid"]
    has_personal_indicator = any(p in q_lower for p in personal_indicators)

    balance_keywords = ["leave balance", "check balance", "view balance", "show balance"]
    is_explicit_balance = any(kw in q_lower for kw in balance_keywords)

    is_leave_balance = (is_explicit_balance or (has_personal_indicator and "leave" in q_lower)) and not is_leave_request and not (has_policy_indicator and not has_personal_indicator)

    # 5. Request Status check
    status_keywords = ["status", "request id", "track leave", "lv1", "lv2", "lv3", "lv4", "lv5", "lv6", "lv7", "lv8", "lv9"]
    req_match = re.search(r'\b(LV\d{4})\b', query, re.IGNORECASE)
    is_leave_status = (req_match is not None) or (("status" in q_lower or "track" in q_lower) and "leave" in q_lower)

    # 6. Employee info check
    emp_keywords = ["who am i", "my profile", "my department", "my manager", "employee details", "employee info"]
    is_emp_info = any(kw in q_lower for kw in emp_keywords)

    # Detect leave type
    detected_type = None
    if "casual" in q_lower:
        detected_type = "casual_leave"
    elif "sick" in q_lower or "medical" in q_lower:
        detected_type = "sick_leave"
    elif "paid" in q_lower or "privilege" in q_lower or "earned" in q_lower:
        detected_type = "paid_leave"

    # Extract dates
    start_date, end_date = extract_dates_from_query(query)

    # Request ID
    req_id = req_match.group(1).upper() if req_match else None

    # Determine intent
    if is_confirm:
        intent = "confirmation"
    elif is_leave_request:
        intent = "leave_request"
    elif is_leave_status:
        intent = "leave_status"
    elif is_leave_balance:
        intent = "leave_balance"
    elif is_emp_info:
        intent = "employee_info"
    elif has_policy_indicator or any(term in q_lower for term in ["policy", "wfh", "travel", "reimbursement", "conduct", "security", "holiday", "handbook", "maternity", "paternity", "notice period", "probation", "bonus", "posh", "how many", "what is"]):
        intent = "policy_question"
    else:
        intent = "policy_question"

    return {
        "intent": intent,
        "is_confirmation": is_confirm,
        "leave_type": detected_type,
        "start_date": start_date,
        "end_date": end_date,
        "request_id": req_id
    }


def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Classify intent and extract request parameters."""
    query = state.get("user_query", "").strip()
    if not query:
        return {
            "intent": "general_question",
            "final_response": "Hello! I am the Roboserv 4i Enterprise Policy Assistant. How can I help you today?"
        }

    # If already confirmed via API flag
    if state.get("confirmed", False):
        return {
            "intent": "leave_request",
            "confirmed": True
        }

    extracted = classify_intent_rule_based(query)
    logger.info(f"Intent classified: {extracted['intent']} for query: '{query}'")

    updates: Dict[str, Any] = {
        "intent": extracted["intent"],
        "sources": [],
        "actions": []
    }

    if extracted["is_confirmation"]:
        updates["confirmed"] = True
        updates["intent"] = "leave_request"

    if extracted["leave_type"] and not state.get("leave_type"):
        updates["leave_type"] = extracted["leave_type"]

    if extracted["start_date"] and not state.get("start_date"):
        updates["start_date"] = extracted["start_date"]

    if extracted["end_date"] and not state.get("end_date"):
        updates["end_date"] = extracted["end_date"]

    if extracted["request_id"] and not state.get("request_id"):
        updates["request_id"] = extracted["request_id"]

    return updates


def policy_question_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Retrieve relevant policy chunks and generate grounded answer with citations."""
    query = state.get("user_query", "")
    logger.info(f"Executing policy RAG retrieval for: '{query}'")

    # Step: search_policy()
    retrieved_chunks = search_policy(query, top_k=5)

    if not retrieved_chunks:
        return {
            "final_response": "I could not find this information in the available company policy documents.",
            "sources": [],
            "retrieved_context": []
        }

    # Step: LLM grounded answer generation
    answer = generate_rag_answer(retrieved_chunks, query)

    # Format sources
    sources = []
    seen = set()
    for chunk in retrieved_chunks:
        key = (chunk.get("source"), chunk.get("page"))
        if key not in seen:
            seen.add(key)
            sources.append({
                "document": chunk.get("source"),
                "page": chunk.get("page"),
                "department": chunk.get("department", "HR"),
                "document_type": chunk.get("document_type", "Policy")
            })

    return {
        "retrieved_context": retrieved_chunks,
        "final_response": answer,
        "sources": sources,
        "actions": []
    }


def leave_balance_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Retrieve leave balance for the employee."""
    emp_id = state.get("employee_id", "EMP001")
    leave_type = state.get("leave_type")

    bal_data = get_leave_balance(emp_id, leave_type)
    if "error" in bal_data:
        return {
            "final_response": f"Error retrieving leave balance: {bal_data['error']}",
            "leave_balance": bal_data
        }

    emp_name = bal_data.get("employee_name", "Employee")
    if leave_type and "balance" in bal_data:
        disp_type = leave_type.replace('_', ' ').title()
        resp = f"{emp_name} ({emp_id}), you currently have **{bal_data['balance']} days** of {disp_type} remaining."
    else:
        resp = (
            f"Here is the current leave balance for **{emp_name}** ({emp_id}):\n\n"
            f"• **Casual Leave:** {bal_data.get('casual_leave', 0)} days\n"
            f"• **Sick Leave:** {bal_data.get('sick_leave', 0)} days\n"
            f"• **Paid Leave:** {bal_data.get('paid_leave', 0)} days"
        )

    return {
        "leave_balance": bal_data,
        "final_response": resp,
        "actions": [{"action": "check_leave_balance", "status": "completed", "details": bal_data}]
    }


def employee_info_node(state: AgentState) -> Dict[str, Any]:
    """Node 4: Retrieve employee details."""
    emp_id = state.get("employee_id", "EMP001")
    emp = get_employee(emp_id)
    if not emp:
        return {
            "final_response": f"Employee record for ID '{emp_id}' was not found in the enterprise database."
        }

    resp = (
        f"**Employee Profile:**\n\n"
        f"• **Employee ID:** {emp['employee_id']}\n"
        f"• **Name:** {emp['name']}\n"
        f"• **Email:** {emp['email']}\n"
        f"• **Department:** {emp['department']}\n"
        f"• **Reporting Manager:** {emp['manager']}"
    )
    return {
        "final_response": resp,
        "actions": [{"action": "lookup_employee", "status": "completed", "details": emp}]
    }


def leave_status_node(state: AgentState) -> Dict[str, Any]:
    """Node 5: Check status of submitted leave request."""
    req_id = state.get("request_id")
    if not req_id:
        # Check from query
        q = state.get("user_query", "")
        m = re.search(r'\b(LV\d{4})\b', q, re.IGNORECASE)
        if m:
            req_id = m.group(1).upper()

    if not req_id:
        return {
            "final_response": "Please specify the leave request ID you would like to track (e.g., 'Check status for LV1025')."
        }

    status_data = get_leave_request_status(req_id)
    if not status_data:
        return {
            "final_response": f"No leave request record found matching ID '{req_id}'."
        }

    resp = (
        f"**Leave Request Details — {req_id}:**\n\n"
        f"• **Employee ID:** {status_data['employee_id']}\n"
        f"• **Leave Type:** {status_data['leave_type'].replace('_', ' ').title()}\n"
        f"• **Period:** {status_data['start_date']} to {status_data['end_date']} ({status_data['days']} working days)\n"
        f"• **Status:** **{status_data['status']}**\n"
        f"• **Submitted At:** {status_data.get('created_at', 'N/A')}"
    )
    return {
        "final_response": resp,
        "actions": [{"action": "get_leave_request_status", "status": "completed", "details": status_data}]
    }


def leave_request_node(state: AgentState) -> Dict[str, Any]:
    """Node 6: Orchestrate the controlled Agentic Leave Request workflow:
    1. Identify employee
    2. Retrieve relevant policy
    3. Check leave balance
    4. Calculate number of days
    5. Check eligibility
    6. Guardrail: Require confirmation before creating request
    7. On confirmation: create_leave_request()
    """
    emp_id = state.get("employee_id", "EMP001")
    start_date = state.get("start_date")
    end_date = state.get("end_date")
    leave_type = normalize_leave_type(state.get("leave_type")) or "casual_leave"
    is_confirmed = state.get("confirmed", False)

    # Verify employee exists
    emp = get_employee(emp_id)
    if not emp:
        return {
            "final_response": f"Employee {emp_id} does not exist in the system.",
            "error": "Employee not found."
        }

    # Verify dates provided
    if not start_date or not end_date:
        return {
            "confirmation_required": False,
            "final_response": (
                "To apply for leave, please provide your start and end dates.\n"
                "Example: *'Apply casual leave from October 5 to October 7.'*"
            )
        }

    # Calculate working days
    calc = calculate_leave_days(start_date, end_date)
    if not calc["valid"]:
        return {
            "confirmation_required": False,
            "final_response": f"Date error: {calc['error']}",
            "error": calc["error"]
        }

    working_days = calc["working_days"]
    norm_start = calc["start_date"]
    norm_end = calc["end_date"]

    # Check eligibility
    eligibility = check_leave_eligibility(emp_id, leave_type, working_days)
    if not eligibility["eligible"]:
        return {
            "confirmation_required": False,
            "requested_days": working_days,
            "eligibility": eligibility,
            "final_response": (
                f"**Leave Request Ineligible:**\n\n"
                f"{eligibility['reason']}\n\n"
                f"Current {leave_type.replace('_', ' ')} balance: {eligibility.get('current_balance', 0)} day(s). "
                f"Requested: {working_days} working day(s)."
            )
        }

    # Retrieve relevant policy citation for grounding
    policy_chunks = search_policy(f"{leave_type} policy working days", top_k=2)
    sources = [
        {"document": c["source"], "page": c["page"], "department": c.get("department", "HR")}
        for c in policy_chunks
    ]

    curr_bal = eligibility["current_balance"]
    remaining_bal = eligibility["remaining_balance"]

    # GUARDRAIL: CONFIRMATION SAFETY
    # If not confirmed yet, ask for confirmation and DO NOT execute state change
    if not is_confirmed:
        resp = (
            f"You are requesting **{working_days} working day(s)** of {leave_type.replace('_', ' ')} "
            f"from **{norm_start}** to **{norm_end}**.\n\n"
            f"• **Current Leave Balance:** {curr_bal} days\n"
            f"• **Requested Duration:** {working_days} days\n"
            f"• **Remaining Balance After Approval:** {remaining_bal} days\n"
            f"• **Status:** Eligible\n\n"
            f"Would you like me to submit this leave request?"
        )
        return {
            "start_date": norm_start,
            "end_date": norm_end,
            "leave_type": leave_type,
            "requested_days": working_days,
            "eligibility": eligibility,
            "confirmation_required": True,
            "confirmed": False,
            "sources": sources,
            "final_response": resp,
            "actions": [{
                "action": "check_leave_eligibility",
                "status": "eligible",
                "details": {
                    "employee_id": emp_id,
                    "leave_type": leave_type,
                    "working_days": working_days,
                    "start_date": norm_start,
                    "end_date": norm_end
                }
            }]
        }

    # User confirmed! Perform state-changing action
    logger.info(f"User confirmed leave request for {emp_id}. Creating leave request in SQLite...")
    created_res = create_leave_request(
        employee_id=emp_id,
        start_date=norm_start,
        end_date=norm_end,
        leave_type=leave_type,
        days=working_days
    )

    if not created_res["success"]:
        return {
            "confirmation_required": False,
            "final_response": f"Failed to submit leave request: {created_res['error']}",
            "error": created_res["error"]
        }

    req_id = created_res["request_id"]
    success_resp = (
        f"Leave request submitted successfully.\n\n"
        f"• **Request ID:** **{req_id}**\n"
        f"• **Employee:** {created_res['employee_name']} ({emp_id})\n"
        f"• **Period:** {norm_start} to {norm_end} ({working_days} working day(s))\n"
        f"• **Leave Type:** {leave_type.replace('_', ' ').title()}\n"
        f"• **Updated Balance:** {created_res['remaining_balance']} day(s)\n"
        f"• **Status:** Pending approval by your manager ({emp['manager']})."
    )

    return {
        "start_date": norm_start,
        "end_date": norm_end,
        "leave_type": leave_type,
        "requested_days": working_days,
        "request_id": req_id,
        "confirmation_required": False,
        "confirmed": True,
        "sources": sources,
        "final_response": success_resp,
        "actions": [{
            "action": "create_leave_request",
            "status": "submitted",
            "details": created_res
        }]
    }


def general_node(state: AgentState) -> Dict[str, Any]:
    """Node 7: General greeting and assistance capabilities."""
    emp_id = state.get("employee_id", "EMP001")
    emp = get_employee(emp_id)
    name_str = f", {emp['name']}" if emp else ""

    resp = (
        f"Hello{name_str}! I am your **Roboserv 4i Enterprise Policy Assistant**.\n\n"
        f"Here are the things I can help you with:\n"
        f"1. **Company Policy Questions (RAG):** Ask about leaves, WFH guidelines, travel per diems, reimbursements, benefits, or the code of conduct.\n"
        f"2. **Check Leave Balance:** Check your remaining casual, sick, or paid leave days.\n"
        f"3. **Apply for Leave:** Apply for leaves (e.g., *'Apply casual leave from October 5 to October 7'*). I will verify your balance and ask for your confirmation before submitting.\n"
        f"4. **Track Leave Request:** Check the status of a submitted request using its ID (e.g., *'Check status for LV1025'*)."
    )
    return {
        "final_response": resp,
        "sources": [],
        "actions": []
    }
