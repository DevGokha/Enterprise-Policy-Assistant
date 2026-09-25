"""Unit tests for HR tools: employee lookup, leave balance, day calculation, eligibility, and requests."""

import pytest
from app.database.database import init_db
from app.database.seed import seed_database
from app.tools.employee_tool import get_employee
from app.tools.leave_tool import (
    get_leave_balance,
    calculate_leave_days,
    check_leave_eligibility
)
from app.tools.request_tool import create_leave_request, get_leave_request_status


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Ensure database schema is initialized and seeded before testing."""
    init_db()
    seed_database()


def test_get_employee_valid():
    """Verify looking up an existing employee returns valid profile."""
    emp = get_employee("EMP001")
    assert emp is not None
    assert emp["employee_id"] == "EMP001"
    assert emp["name"] == "Dev Kumar"
    assert emp["department"] == "AI/ML"
    assert "Rahul Sharma" in emp["manager"]


def test_get_employee_invalid():
    """Verify non-existent employee returns None."""
    emp = get_employee("EMP999")
    assert emp is None


def test_get_leave_balance_all():
    """Verify retrieving all leave balances for an employee."""
    bal = get_leave_balance("EMP001")
    assert "error" not in bal
    assert bal["employee_id"] == "EMP001"
    assert "casual_leave" in bal
    assert "sick_leave" in bal
    assert "paid_leave" in bal
    assert bal["casual_leave"] >= 0


def test_get_leave_balance_specific():
    """Verify retrieving a specific leave balance type."""
    bal = get_leave_balance("EMP001", "casual_leave")
    assert "error" not in bal
    assert bal["leave_type"] == "casual_leave"
    assert "balance" in bal


def test_calculate_leave_days_midweek():
    """Calculate working days between Monday and Wednesday (3 working days)."""
    # 2026-10-05 is Monday, 2026-10-07 is Wednesday
    res = calculate_leave_days("2026-10-05", "2026-10-07")
    assert res["valid"] is True
    assert res["working_days"] == 3
    assert res["weekend_days"] == 0


def test_calculate_leave_days_across_weekend():
    """Calculate working days spanning a weekend (Friday to Tuesday = 3 working days)."""
    # 2026-10-09 is Friday, 2026-10-13 is Tuesday (Sat & Sun excluded)
    res = calculate_leave_days("2026-10-09", "2026-10-13")
    assert res["valid"] is True
    assert res["working_days"] == 3
    assert res["weekend_days"] == 2


def test_calculate_leave_days_invalid_order():
    """Ensure start_date after end_date is caught and marked invalid."""
    res = calculate_leave_days("2026-10-10", "2026-10-05")
    assert res["valid"] is False
    assert "cannot be after" in res["error"]


def test_calculate_leave_days_invalid_string():
    """Ensure unparseable strings return a friendly error."""
    res = calculate_leave_days("not-a-date", "2026-10-05")
    assert res["valid"] is False
    assert "Invalid date format" in res["error"]


def test_check_leave_eligibility_success():
    """Verify eligibility when employee has sufficient balance."""
    elig = check_leave_eligibility("EMP002", "casual_leave", 2)
    assert elig["eligible"] is True
    assert elig["requested_days"] == 2
    assert elig["remaining_balance"] >= 0


def test_check_leave_eligibility_insufficient_balance():
    """Verify rejection when requested days exceed available balance."""
    elig = check_leave_eligibility("EMP001", "casual_leave", 50)
    assert elig["eligible"] is False
    assert "Insufficient" in elig["reason"]


def test_check_leave_eligibility_zero_days():
    """Verify rejection when requested days are zero or negative."""
    elig = check_leave_eligibility("EMP001", "casual_leave", 0)
    assert elig["eligible"] is False
    assert "greater than zero" in elig["reason"]


def test_create_leave_request_and_status():
    """Verify leave request submission, balance deduction, and status retrieval."""
    init_bal = get_leave_balance("EMP004", "casual_leave")["balance"]
    assert init_bal >= 2

    # Create request for 2 days
    res = create_leave_request(
        employee_id="EMP004",
        start_date="2026-11-02",
        end_date="2026-11-03",
        leave_type="casual_leave",
        days=2
    )

    assert res["success"] is True
    req_id = res["request_id"]
    assert req_id.startswith("LV")
    assert res["remaining_balance"] == init_bal - 2

    # Verify status query
    status_data = get_leave_request_status(req_id)
    assert status_data is not None
    assert status_data["request_id"] == req_id
    assert status_data["employee_id"] == "EMP004"
    assert status_data["status"] == "Pending"
    assert status_data["days"] == 2
