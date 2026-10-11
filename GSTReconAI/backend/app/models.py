"""SQLAlchemy models for GSTRecon AI."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    accountant = "accountant"


class JobStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.accountant, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    clients = relationship("Client", back_populates="owner")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    gstin = Column(String(16), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="clients")
    jobs = relationship("ReconciliationJob", back_populates="client")


class ReconciliationJob(Base):
    __tablename__ = "reconciliation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.pending, nullable=False)
    total_invoices = Column(Integer, default=0)
    match_count = Column(Integer, default=0)
    mismatch_count = Column(Integer, default=0)
    missing_count = Column(Integer, default=0)
    extra_count = Column(Integer, default=0)
    purchase_itc_total = Column(Integer, default=0)
    gstr2b_itc_total = Column(Integer, default=0)
    purchase_path = Column(Text, nullable=False)
    gstr2b_path = Column(Text, nullable=False)
    report_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)

    client = relationship("Client", back_populates="jobs")
