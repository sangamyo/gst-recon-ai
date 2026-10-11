"""Client management endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import ClientCreate, ClientRead, JobRead

router = APIRouter(prefix="/clients", tags=["clients"])


def _assert_client_access(client: models.Client, user: models.User):
    if user.role == models.UserRole.admin:
        return
    if client.user_id != user.id:
        raise HTTPException(status_code=403, detail="Client access denied")


# Registered both with and without a trailing slash so the frontend's POST /clients
# does not trigger a 307 redirect (which breaks behind HTTPS proxies / CORS).
@router.post("", response_model=ClientRead)
@router.post("/", response_model=ClientRead, include_in_schema=False)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    client = models.Client(name=payload.name, gstin=payload.gstin.upper(), user_id=current_user.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=List[ClientRead])
@router.get("/", response_model=List[ClientRead], include_in_schema=False)
def list_clients(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Client)
    if current_user.role != models.UserRole.admin:
        query = query.filter(models.Client.user_id == current_user.id)
    return query.order_by(models.Client.created_at.desc()).all()


@router.get("/{client_id}/jobs", response_model=List[JobRead])
def list_client_jobs(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    _assert_client_access(client, current_user)
    return (
        db.query(models.ReconciliationJob)
        .filter(models.ReconciliationJob.client_id == client_id)
        .order_by(models.ReconciliationJob.created_at.desc())
        .all()
    )
