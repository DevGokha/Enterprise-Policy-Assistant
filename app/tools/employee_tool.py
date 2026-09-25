"""Employee tool for looking up employee details in the database."""

import logging
from typing import Optional, Dict, Any
from app.database.database import SessionLocal
from app.database.models import Employee

logger = logging.getLogger(__name__)


def get_employee(employee_id: str) -> Optional[Dict[str, Any]]:
    """Lookup employee details by employee ID.
    
    Args:
        employee_id: Unique identifier for employee (e.g., 'EMP001').
        
    Returns:
        Dictionary of employee data (id, name, email, department, manager) or None if not found.
    """
    if not employee_id:
        return None

    db = SessionLocal()
    try:
        emp = db.query(Employee).filter(Employee.employee_id == employee_id.strip().upper()).first()
        if emp:
            logger.info(f"Retrieved employee {emp.employee_id} ({emp.name})")
            return emp.to_dict()
        logger.warning(f"Employee {employee_id} not found in database.")
        return None
    except Exception as e:
        logger.error(f"Error querying employee {employee_id}: {e}")
        return None
    finally:
        db.close()
