"""Database models for Enterprise Policy Assistant."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Employee(Base):
    """Employee record table."""
    __tablename__ = "employees"

    employee_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    department = Column(String(100), nullable=False)
    manager = Column(String(100), nullable=False)

    leave_balance = relationship("LeaveBalance", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "manager": self.manager
        }


class LeaveBalance(Base):
    """Leave balance table per employee."""
    __tablename__ = "leave_balance"

    employee_id = Column(String(50), ForeignKey("employees.employee_id"), primary_key=True)
    casual_leave = Column(Integer, default=12, nullable=False)
    sick_leave = Column(Integer, default=10, nullable=False)
    paid_leave = Column(Integer, default=18, nullable=False)

    employee = relationship("Employee", back_populates="leave_balance")

    def to_dict(self):
        return {
            "employee_id": self.employee_id,
            "casual_leave": self.casual_leave,
            "sick_leave": self.sick_leave,
            "paid_leave": self.paid_leave
        }


class LeaveRequest(Base):
    """Submitted leave requests table."""
    __tablename__ = "leave_requests"

    request_id = Column(String(50), primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False, index=True)
    start_date = Column(String(20), nullable=False)
    end_date = Column(String(20), nullable=False)
    leave_type = Column(String(50), nullable=False)
    days = Column(Integer, nullable=False)
    status = Column(String(50), default="Pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    employee = relationship("Employee", back_populates="leave_requests")

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "employee_id": self.employee_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "leave_type": self.leave_type,
            "days": self.days,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
