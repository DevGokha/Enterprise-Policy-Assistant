"""Leave management tools: balance lookup, working day calculation, eligibility check."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.database.database import SessionLocal
from app.database.models import LeaveBalance, Employee

logger = logging.getLogger(__name__)

VALID_LEAVE_TYPES = {
    "casual": "casual_leave",
    "casual_leave": "casual_leave",
    "casual leave": "casual_leave",
    "sick": "sick_leave",
    "sick_leave": "sick_leave",
    "sick leave": "sick_leave",
    "paid": "paid_leave",
    "paid_leave": "paid_leave",
    "paid leave": "paid_leave",
    "earned": "paid_leave",
    "privilege": "paid_leave"
}


def normalize_leave_type(leave_type_input: Optional[str]) -> Optional[str]:
    """Normalize user or model leave type strings to column names."""
    if not leave_type_input:
        return None
    cleaned = leave_type_input.strip().lower()
    return VALID_LEAVE_TYPES.get(cleaned, cleaned)


def get_leave_balance(employee_id: str, leave_type: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve leave balance for a given employee.
    
    Args:
        employee_id: Employee ID (e.g., 'EMP001').
        leave_type: Optional specific leave type ('casual_leave', 'sick_leave', 'paid_leave').
        
    Returns:
        Dictionary containing balances or an error message.
    """
    if not employee_id:
        return {"error": "Employee ID is required."}

    norm_id = employee_id.strip().upper()
    db = SessionLocal()
    try:
        emp = db.query(Employee).filter(Employee.employee_id == norm_id).first()
        if not emp:
            return {"error": f"Employee {norm_id} not found."}

        balance = db.query(LeaveBalance).filter(LeaveBalance.employee_id == norm_id).first()
        if not balance:
            return {"error": f"Leave balance record not found for {norm_id}."}

        norm_type = normalize_leave_type(leave_type)
        if norm_type:
            val = getattr(balance, norm_type, None)
            if val is not None:
                return {
                    "employee_id": norm_id,
                    "employee_name": emp.name,
                    "leave_type": norm_type,
                    "balance": val,
                    "all_balances": balance.to_dict()
                }
            return {
                "error": f"Invalid leave type '{leave_type}'. Valid types: casual_leave, sick_leave, paid_leave.",
                "all_balances": balance.to_dict()
            }

        return {
            "employee_id": norm_id,
            "employee_name": emp.name,
            "casual_leave": balance.casual_leave,
            "sick_leave": balance.sick_leave,
            "paid_leave": balance.paid_leave
        }
    except Exception as e:
        logger.error(f"Error fetching leave balance for {norm_id}: {e}")
        return {"error": str(e)}
    finally:
        db.close()


def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse flexible date strings into datetime object."""
    if not date_str:
        return None
    cleaned = date_str.strip()
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d",
        "%b %d",
        "%d %B %Y",
        "%d %b %Y",
        "%d %B",
        "%d %b",
    ]
    current_year = datetime.now().year
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if dt.year == 1900:  # Format without year
                dt = dt.replace(year=current_year)
            return dt
        except ValueError:
            continue
    return None


def calculate_leave_days(start_date: str, end_date: str) -> Dict[str, Any]:
    """Calculate the number of working days between start_date and end_date (inclusive),
    excluding Saturdays and Sundays.
    
    Args:
        start_date: Start date string (e.g. '2026-10-05' or 'October 5').
        end_date: End date string (e.g. '2026-10-07' or 'October 7').
        
    Returns:
        Dictionary with working_days, total_days, breakdown, and validity.
    """
    dt_start = parse_date_string(start_date)
    dt_end = parse_date_string(end_date)

    if not dt_start or not dt_end:
        return {
            "valid": False,
            "error": f"Invalid date format. Unable to parse '{start_date}' or '{end_date}'. Please use YYYY-MM-DD.",
            "working_days": 0
        }

    if dt_start > dt_end:
        return {
            "valid": False,
            "error": f"Start date ({dt_start.strftime('%Y-%m-%d')}) cannot be after end date ({dt_end.strftime('%Y-%m-%d')}).",
            "working_days": 0
        }

    working_days = 0
    weekend_days = 0
    curr = dt_start
    while curr <= dt_end:
        # Monday is 0 and Sunday is 6. 5 is Saturday, 6 is Sunday.
        if curr.weekday() in (5, 6):
            weekend_days += 1
        else:
            working_days += 1
        curr += timedelta(days=1)

    total_calendar_days = (dt_end - dt_start).days + 1

    return {
        "valid": True,
        "start_date": dt_start.strftime("%Y-%m-%d"),
        "end_date": dt_end.strftime("%Y-%m-%d"),
        "working_days": working_days,
        "weekend_days": weekend_days,
        "total_calendar_days": total_calendar_days
    }


def check_leave_eligibility(employee_id: str, leave_type: str, days: int) -> Dict[str, Any]:
    """Check if the employee has sufficient balance and complies with basic leave rules.
    
    Args:
        employee_id: Employee ID (e.g. 'EMP001').
        leave_type: Type of leave ('casual_leave', 'sick_leave', 'paid_leave').
        days: Number of working days requested.
        
    Returns:
        Dictionary with eligible (bool), reason, current_balance, requested_days.
    """
    if days <= 0:
        return {
            "eligible": False,
            "reason": "Requested leave days must be greater than zero.",
            "requested_days": days,
            "current_balance": 0
        }

    norm_type = normalize_leave_type(leave_type)
    if not norm_type:
        return {
            "eligible": False,
            "reason": f"Unknown leave type '{leave_type}'. Allowed types: casual_leave, sick_leave, paid_leave.",
            "requested_days": days,
            "current_balance": 0
        }

    balance_res = get_leave_balance(employee_id, norm_type)
    if "error" in balance_res:
        return {
            "eligible": False,
            "reason": balance_res["error"],
            "requested_days": days,
            "current_balance": 0
        }

    current_balance = balance_res["balance"]
    if current_balance < days:
        return {
            "eligible": False,
            "reason": f"Insufficient {norm_type.replace('_', ' ')} balance. Available: {current_balance} days, Requested: {days} days.",
            "requested_days": days,
            "current_balance": current_balance,
            "leave_type": norm_type
        }

    return {
        "eligible": True,
        "reason": f"Eligible for {days} day(s) of {norm_type.replace('_', ' ')}. Remaining balance after leave will be {current_balance - days} day(s).",
        "requested_days": days,
        "current_balance": current_balance,
        "remaining_balance": current_balance - days,
        "leave_type": norm_type
    }
