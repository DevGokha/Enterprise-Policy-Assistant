"""Seed script to populate initial sample employees and leave balances."""

import logging
from app.database.database import SessionLocal, init_db
from app.database.models import Employee, LeaveBalance, LeaveRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_EMPLOYEES = [
    {
        "employee_id": "EMP001",
        "name": "Dev Kumar",
        "email": "dev@roboserv4i.com",
        "department": "AI/ML",
        "manager": "Rahul Sharma",
        "balances": {"casual_leave": 8, "sick_leave": 7, "paid_leave": 15}
    },
    {
        "employee_id": "EMP002",
        "name": "Priya Sharma",
        "email": "priya@roboserv4i.com",
        "department": "Cloud Architecture",
        "manager": "Anita Desai",
        "balances": {"casual_leave": 10, "sick_leave": 9, "paid_leave": 18}
    },
    {
        "employee_id": "EMP003",
        "name": "Rohan Verma",
        "email": "rohan@roboserv4i.com",
        "department": "Frontend Engineering",
        "manager": "Rahul Sharma",
        "balances": {"casual_leave": 4, "sick_leave": 5, "paid_leave": 12}
    },
    {
        "employee_id": "EMP004",
        "name": "Ananya Iyer",
        "email": "ananya@roboserv4i.com",
        "department": "Human Resources",
        "manager": "Vikram Malhotra",
        "balances": {"casual_leave": 11, "sick_leave": 8, "paid_leave": 16}
    },
    {
        "employee_id": "EMP005",
        "name": "Vikram Malhotra",
        "email": "vikram@roboserv4i.com",
        "department": "Human Resources",
        "manager": "Executive Office",
        "balances": {"casual_leave": 12, "sick_leave": 10, "paid_leave": 18}
    },
]


def seed_database():
    """Seed sample data into SQLite."""
    init_db()
    db = SessionLocal()
    try:
        logger.info("Seeding database with sample employee records...")
        for data in SAMPLE_EMPLOYEES:
            existing = db.query(Employee).filter(Employee.employee_id == data["employee_id"]).first()
            if not existing:
                emp = Employee(
                    employee_id=data["employee_id"],
                    name=data["name"],
                    email=data["email"],
                    department=data["department"],
                    manager=data["manager"]
                )
                db.add(emp)
                db.flush()

                bal = LeaveBalance(
                    employee_id=data["employee_id"],
                    casual_leave=data["balances"]["casual_leave"],
                    sick_leave=data["balances"]["sick_leave"],
                    paid_leave=data["balances"]["paid_leave"]
                )
                db.add(bal)
                logger.info(f"Added employee {data['employee_id']} - {data['name']}")
            else:
                existing_bal = db.query(LeaveBalance).filter(LeaveBalance.employee_id == data["employee_id"]).first()
                if existing_bal:
                    existing_bal.casual_leave = data["balances"]["casual_leave"]
                    existing_bal.sick_leave = data["balances"]["sick_leave"]
                    existing_bal.paid_leave = data["balances"]["paid_leave"]
                logger.info(f"Refreshed employee {data['employee_id']} balances.")

        db.commit()
        logger.info("Database seeding completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
