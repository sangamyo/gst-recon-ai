"""Pydantic schemas for API contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

from app.models import JobStatus, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.accountant


class UserCreate(UserBase):
    password: Annotated[str, StringConstraints(min_length=8, max_length=72)]


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientBase(BaseModel):
    name: str
    gstin: Annotated[str, StringConstraints(strip_whitespace=True, min_length=15, max_length=15)]


class ClientCreate(ClientBase):
    pass


class ClientRead(ClientBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobRead(BaseModel):
    id: int
    client_id: int
    status: JobStatus
    total_invoices: int
    match_count: int
    mismatch_count: int
    missing_count: int
    extra_count: int
    purchase_itc_total: int
    gstr2b_itc_total: int
    report_path: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardMetrics(BaseModel):
    total_clients: int
    total_invoices: int
    match_ratio: float
    mismatch_ratio: float
    missing_ratio: float
    total_itc_purchase: float
    total_itc_2b: float
    difference: float


class JobTriggerResponse(BaseModel):
    job_id: int
    status: JobStatus


class RiskSupplier(BaseModel):
    supplier_gstin: str
    mismatch_count: int
    tax_gap: float


class MonthlyTrend(BaseModel):
    month: str
    match_count: int
    mismatch_count: int
