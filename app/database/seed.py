"""Seed script to populate initial sample employees and leave balances."""

import logging
from app.database.database import SessionLocal, init_db
from app.database.models import Employee, LeaveBalance, LeaveRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_EMPLOYEES = [
    {
        "employee_id": "EMP001",
        "name": "Abhishek Koli",
        "email": "abhishek.koli@roboserv4i.com",
        "department": "Electrical & Embedded",
        "manager": "Executive Office",
        "balances": {"casual_leave": 10, "sick_leave": 8, "paid_leave": 15}
    },
    {
        "employee_id": "EMP002",
        "name": "Raj Teli",
        "email": "raj.teli@roboserv4i.com",
        "department": "Robotic & Software Engg",
        "manager": "Executive Office",
        "balances": {"casual_leave": 12, "sick_leave": 9, "paid_leave": 18}
    },
    {
        "employee_id": "EMP003",
        "name": "Hrutvik Owal",
        "email": "hrutvik.owal@roboserv4i.com",
        "department": "Robotic-Design",
        "manager": "Raj Teli",
        "balances": {"casual_leave": 10, "sick_leave": 7, "paid_leave": 14}
    },
    {
        "employee_id": "EMP004",
        "name": "Santosh Barai",
        "email": "santosh.barai@roboserv4i.com",
        "department": "Robotic-Design",
        "manager": "Raj Teli",
        "balances": {"casual_leave": 11, "sick_leave": 8, "paid_leave": 16}
    },
    {
        "employee_id": "EMP005",
        "name": "Divyansh Jha",
        "email": "divyansh.jha@roboserv4i.com",
        "department": "Electronics & IOT",
        "manager": "Abhishek Koli",
        "balances": {"casual_leave": 9, "sick_leave": 7, "paid_leave": 15}
    },
    {
        "employee_id": "EMP006",
        "name": "Dev Gokha",
        "email": "dev.gokha@roboserv4i.com",
        "department": "Software Developer",
        "manager": "Raj Teli",
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
                existing.name = data["name"]
                existing.email = data["email"]
                existing.department = data["department"]
                existing.manager = data["manager"]
                existing_bal = db.query(LeaveBalance).filter(LeaveBalance.employee_id == data["employee_id"]).first()
                if existing_bal:
                    existing_bal.casual_leave = data["balances"]["casual_leave"]
                    existing_bal.sick_leave = data["balances"]["sick_leave"]
                    existing_bal.paid_leave = data["balances"]["paid_leave"]
                else:
                    new_bal = LeaveBalance(
                        employee_id=data["employee_id"],
                        casual_leave=data["balances"]["casual_leave"],
                        sick_leave=data["balances"]["sick_leave"],
                        paid_leave=data["balances"]["paid_leave"]
                    )
                    db.add(new_bal)
                logger.info(f"Updated employee {data['employee_id']} - {data['name']}")

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
