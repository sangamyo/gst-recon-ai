"""Job status, dashboard metrics, and report delivery endpoints."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import DashboardMetrics, JobRead, MonthlyTrend, RiskSupplier

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])
settings = get_settings()


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    job = db.get(models.ReconciliationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    client = db.get(models.Client, job.client_id)
    if current_user.role != models.UserRole.admin and client.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return job


@router.get("/jobs/{job_id}/report")
def download_report(job_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    job = db.get(models.ReconciliationJob, job_id)
    if not job or not job.report_path:
        raise HTTPException(status_code=404, detail="Report not found")
    client = db.get(models.Client, job.client_id)
    if current_user.role != models.UserRole.admin and client.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if job.status != models.JobStatus.completed:
        raise HTTPException(status_code=409, detail="Report not ready yet")
    path = Path(job.report_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Report missing on disk")
    return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/dashboard/metrics", response_model=DashboardMetrics)
def dashboard_metrics(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    total_clients = db.query(models.Client)
    if current_user.role != models.UserRole.admin:
        total_clients = total_clients.filter(models.Client.user_id == current_user.id)
    total_clients = total_clients.count()

    jobs_query = db.query(models.ReconciliationJob)
    if current_user.role != models.UserRole.admin:
        jobs_query = jobs_query.join(models.Client).filter(models.Client.user_id == current_user.id)

    aggregate = jobs_query.with_entities(
        func.coalesce(func.sum(models.ReconciliationJob.match_count), 0),
        func.coalesce(func.sum(models.ReconciliationJob.mismatch_count), 0),
        func.coalesce(func.sum(models.ReconciliationJob.missing_count), 0),
        func.coalesce(func.sum(models.ReconciliationJob.purchase_itc_total), 0),
        func.coalesce(func.sum(models.ReconciliationJob.gstr2b_itc_total), 0),
        func.coalesce(func.sum(models.ReconciliationJob.total_invoices), 0),
    ).first()

    match_sum, mismatch_sum, missing_sum, purchase_sum, gstr_sum, invoices_sum = aggregate
    denominator = max(invoices_sum, 1)

    return DashboardMetrics(
        total_clients=total_clients,
        total_invoices=int(invoices_sum),
        match_ratio=float(match_sum) / denominator,
        mismatch_ratio=float(mismatch_sum) / denominator,
        missing_ratio=float(missing_sum) / denominator,
        total_itc_purchase=float(purchase_sum),
        total_itc_2b=float(gstr_sum),
        difference=float(purchase_sum - gstr_sum),
    )


@router.get("/dashboard/top-risk", response_model=List[RiskSupplier])
def top_risk_suppliers(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    jobs = db.query(models.ReconciliationJob).join(models.Client)
    if current_user.role != models.UserRole.admin:
        jobs = jobs.filter(models.Client.user_id == current_user.id)

    # Simplified: derive from stored mismatch counts per client.
    results = (
        jobs.with_entities(models.Client.gstin, func.sum(models.ReconciliationJob.mismatch_count))
        .group_by(models.Client.gstin)
        .order_by(func.sum(models.ReconciliationJob.mismatch_count).desc())
        .limit(5)
        .all()
    )
    return [
        RiskSupplier(supplier_gstin=row[0], mismatch_count=int(row[1] or 0), tax_gap=float(row[1] or 0))
        for row in results
    ]


@router.get("/dashboard/monthly-trend", response_model=List[MonthlyTrend])
def monthly_trend(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    jobs = db.query(models.ReconciliationJob)
    if current_user.role != models.UserRole.admin:
        jobs = jobs.join(models.Client).filter(models.Client.user_id == current_user.id)

    # Aggregate in Python so this works on both PostgreSQL and SQLite.
    buckets: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    rows = jobs.with_entities(
        models.ReconciliationJob.created_at,
        models.ReconciliationJob.match_count,
        models.ReconciliationJob.mismatch_count,
    ).all()
    for created_at, match_count, mismatch_count in rows:
        month = (created_at or datetime.utcnow()).strftime("%Y-%m")
        buckets[month][0] += int(match_count or 0)
        buckets[month][1] += int(mismatch_count or 0)

    return [
        MonthlyTrend(month=month, match_count=counts[0], mismatch_count=counts[1])
        for month, counts in sorted(buckets.items())
    ]
