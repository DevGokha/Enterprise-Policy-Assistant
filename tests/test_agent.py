"""Unit tests for the LangGraph agent workflow with mocked LLM."""

import pytest
from unittest.mock import patch

from app.database.database import init_db
from app.database.seed import seed_database
from app.agent.graph import run_agent_workflow
from app.tools.leave_tool import get_leave_balance


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    seed_database()


def test_agent_policy_question_routing():
    """Verify policy questions route to policy_handler and return sources."""
    query = "What is the policy for working from home?"
    res = run_agent_workflow(query=query, employee_id="EMP001")

    assert res["intent"] == "policy_question"
    assert "final_response" in res
    assert len(res["final_response"]) > 0
    # If indexed, verify sources; if not indexed yet, verify friendly fallback
    if res.get("sources"):
        assert res["sources"][0]["document"].endswith(".pdf")
        assert "page" in res["sources"][0]


def test_agent_leave_balance_question():
    """Verify leave balance questions route to balance_handler and query DB."""
    query = "How many casual leaves do I have?"
    res = run_agent_workflow(query=query, employee_id="EMP001")

    assert res["intent"] == "leave_balance"
    assert "casual" in res["final_response"].lower()
    assert "Abhishek Koli" in res["final_response"] or "EMP001" in res["final_response"]
    assert len(res["actions"]) > 0
    assert res["actions"][0]["action"] == "check_leave_balance"


def test_agent_leave_request_confirmation_safety_flow():
    """Verify complete leave request flow:
    1. Unconfirmed request triggers eligibility check and demands confirmation without state change.
    2. Explicit confirmation triggers create_leave_request and returns request_id.
    """
    emp_id = "EMP003"
    initial_bal = get_leave_balance(emp_id, "casual_leave")["balance"]
    assert initial_bal >= 2

    # Step 1: User asks to apply leave
    query = "Apply casual leave from October 5 to October 7"
    res1 = run_agent_workflow(query=query, employee_id=emp_id, confirmed=False)

    assert res1["intent"] == "leave_request"
    assert res1["confirmation_required"] is True
    assert res1["confirmed"] is False
    assert res1["requested_days"] == 3
    assert "Would you like me to submit" in res1["final_response"]

    # CRITICAL: Verify balance was NOT deducted before confirmation
    mid_bal = get_leave_balance(emp_id, "casual_leave")["balance"]
    assert mid_bal == initial_bal

    # Step 2: User confirms the request
    res2 = run_agent_workflow(
        query="Yes, submit it.",
        employee_id=emp_id,
        confirmed=True,
        extra_state={
            "start_date": res1["start_date"],
            "end_date": res1["end_date"],
            "leave_type": res1["leave_type"],
            "requested_days": res1["requested_days"]
        }
    )

    assert res2["confirmed"] is True
    assert res2["confirmation_required"] is False
    assert res2["request_id"] is not None
    assert res2["request_id"].startswith("LV")
    assert "submitted successfully" in res2["final_response"].lower()

    # Verify balance was decremented by 3
    final_bal = get_leave_balance(emp_id, "casual_leave")["balance"]
    assert final_bal == initial_bal - 3


def test_agent_invalid_dates_error():
    """Verify agent catches invalid leave date ranges and returns a helpful error."""
    query = "Apply casual leave from 2026-10-15 to 2026-10-10"
    res = run_agent_workflow(query=query, employee_id="EMP001")

    assert res["confirmation_required"] is False
    assert "Date error" in res["final_response"] or "cannot be after" in res["final_response"]
