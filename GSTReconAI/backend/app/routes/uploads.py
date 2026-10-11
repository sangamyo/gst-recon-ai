"""File upload and job trigger endpoints."""
from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import JobTriggerResponse
from app.services.recon_engine import reconcile_job, run_reconciliation
from app.utils.file_validator import (
    REQUIRED_2B_COLUMNS,
    REQUIRED_PURCHASE_COLUMNS,
    ValidationError,
    validate_excel,
)
from app.utils.logger import logger

router = APIRouter(prefix="/clients", tags=["uploads"])
settings = get_settings()


def _save_upload(upload: UploadFile, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return dest


@router.post("/{client_id}/jobs", response_model=JobTriggerResponse)
def create_reconciliation_job(
    client_id: int,
    background_tasks: BackgroundTasks,
    purchase_file: UploadFile = File(...),
    gstr2b_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if current_user.role != models.UserRole.admin and client.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Client access denied")

    job_dir = Path(settings.storage_dir) / f"client_{client_id}" / uuid4().hex
    purchase_path = job_dir / "purchase.xlsx"
    gstr2b_path = job_dir / "gstr2b.xlsx"

    _save_upload(purchase_file, purchase_path)
    _save_upload(gstr2b_file, gstr2b_path)

    # Validate immediately for user feedback
    try:
        validate_excel(purchase_path, REQUIRED_PURCHASE_COLUMNS)
        validate_excel(gstr2b_path, REQUIRED_2B_COLUMNS)
    except ValidationError as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job = models.ReconciliationJob(
        client_id=client_id,
        status=models.JobStatus.pending,
        purchase_path=str(purchase_path),
        gstr2b_path=str(gstr2b_path),
        report_path=str(job_dir),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if settings.use_celery:
        try:
            reconcile_job.delay(job.id)
        except Exception:  # broker unreachable -> fall back to in-process execution
            logger.exception("Celery dispatch failed for job {}; running in-process", job.id)
            background_tasks.add_task(run_reconciliation, job.id)
    else:
        # No Redis configured: run after the response is sent, inside this API process.
        background_tasks.add_task(run_reconciliation, job.id)
    return JobTriggerResponse(job_id=job.id, status=job.status)
