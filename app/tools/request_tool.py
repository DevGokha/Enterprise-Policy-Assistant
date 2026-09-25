"""Leave request creation and status tracking tool."""

import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional
from app.database.database import SessionLocal
from app.database.models import LeaveRequest, LeaveBalance, Employee
from app.tools.leave_tool import normalize_leave_type

logger = logging.getLogger(__name__)


def generate_request_id() -> str:
    """Generate a clean enterprise request ID like LV1024."""
    num = random.randint(1000, 9999)
    return f"LV{num}"


def create_leave_request(
    employee_id: str,
    start_date: str,
    end_date: str,
    leave_type: str,
    days: int
) -> Dict[str, Any]:
    """Create a leave request in the database and deduct the balance.
    
    CRITICAL SAFETY GUARDRAILS:
    - Never creates leave without verifying balance.
    - Prevents negative balances.
    - Atomically updates balance and creates request record.
    """
    if not employee_id:
        return {"success": False, "error": "Employee ID is required."}

    norm_id = employee_id.strip().upper()
    norm_type = normalize_leave_type(leave_type)
    if not norm_type:
        return {"success": False, "error": f"Invalid leave type: {leave_type}"}

    if days <= 0:
        return {"success": False, "error": "Requested leave days must be greater than zero."}

    db = SessionLocal()
    try:
        emp = db.query(Employee).filter(Employee.employee_id == norm_id).first()
        if not emp:
            return {"success": False, "error": f"Employee {norm_id} not found."}

        balance = db.query(LeaveBalance).filter(LeaveBalance.employee_id == norm_id).first()
        if not balance:
            return {"success": False, "error": f"Leave balance record not found for {norm_id}."}

        current_val = getattr(balance, norm_type, 0)
        if current_val < days:
            return {
                "success": False,
                "error": f"Insufficient {norm_type.replace('_', ' ')} balance ({current_val} available, {days} requested)."
            }

        # Deduct balance
        setattr(balance, norm_type, current_val - days)

        # Generate unique request ID
        req_id = generate_request_id()
        while db.query(LeaveRequest).filter(LeaveRequest.request_id == req_id).first():
            req_id = generate_request_id()

        leave_req = LeaveRequest(
            request_id=req_id,
            employee_id=norm_id,
            start_date=start_date,
            end_date=end_date,
            leave_type=norm_type,
            days=days,
            status="Pending",
            created_at=datetime.utcnow()
        )
        db.add(leave_req)
        db.commit()
        db.refresh(leave_req)

        logger.info(f"Created leave request {req_id} for {norm_id} ({days} days of {norm_type})")
        return {
            "success": True,
            "request_id": req_id,
            "employee_id": norm_id,
            "employee_name": emp.name,
            "leave_type": norm_type,
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "status": "Pending",
            "remaining_balance": getattr(balance, norm_type),
            "message": f"Leave request {req_id} submitted successfully and is pending approval."
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating leave request for {norm_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_leave_request_status(request_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the status and details of a submitted leave request by ID.
    
    Args:
        request_id: Unique request identifier (e.g., 'LV1025').
        
    Returns:
        Dictionary of request details or None if not found.
    """
    if not request_id:
        return None

    clean_id = request_id.strip().upper()
    db = SessionLocal()
    try:
        req = db.query(LeaveRequest).filter(LeaveRequest.request_id == clean_id).first()
        if not req:
            logger.warning(f"Leave request {clean_id} not found.")
            return None
        return req.to_dict()
    except Exception as e:
        logger.error(f"Error fetching status for request {clean_id}: {e}")
        return None
    finally:
        db.close()


def get_employee_leave_requests(employee_id: str, limit: int = 10) -> list:
    """Retrieve recent leave requests for a given employee.
    
    Args:
        employee_id: Employee identifier (e.g., 'EMP006').
        limit: Maximum number of recent requests to return.
        
    Returns:
        List of dictionaries with leave request details.
    """
    if not employee_id:
        return []

    clean_id = employee_id.strip().upper()
    db = SessionLocal()
    try:
        reqs = (
            db.query(LeaveRequest)
            .filter(LeaveRequest.employee_id == clean_id)
            .order_by(LeaveRequest.created_at.desc())
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in reqs]
    except Exception as e:
        logger.error(f"Error fetching requests for employee {clean_id}: {e}")
        return []
    finally:
        db.close()

