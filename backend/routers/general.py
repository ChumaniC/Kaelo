# backend/routers/general.py
from venv import logger

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, or_, func
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_database
from backend.schemas import EventOut, AuditEntry
from backend.models import Event, Animal, AuditLog

router = APIRouter(prefix="/general", tags=["general"])

@router.get(
    "/animals/{tag_id}/history",
    response_model=List[AuditEntry],
    summary="Get full on‑chain history for an animal",
)
def animal_history(tag_id: str, db: Session = Depends(get_database)):
    # (optional) verify that tag exists in your DB
    if not db.query(Animal).filter_by(tag_id=tag_id).first():
        raise HTTPException(404, f"Animal {tag_id} not found")

    entries = (
        db.query(AuditLog, Event.event_type)
        .join(Event, AuditLog.event_id == Event.event_id)
          .filter(
            or_(
              # top‑level animalId in the HCS payload is actually the tag!
                func.jsonb_extract_path_text(AuditLog.payload, "animalId") == tag_id,
                func.jsonb_extract_path_text(AuditLog.payload, "offspringAnimalId") == tag_id,
                func.jsonb_extract_path_text(AuditLog.payload, "motherAnimalId") == tag_id,
            )
          )
          .order_by(desc(AuditLog.consensus_timestamp))
          .all()
    )

    out: List[AuditEntry] = []
    for audit, ev_type in entries:
        out.append(
            AuditEntry(
                event_id=audit.event_id,
                event_type=ev_type,
                hcs_transaction_id=audit.hcs_transaction_id,
                consensus_timestamp=audit.consensus_timestamp,
                payload=audit.payload,
            )
        )
    return out

@router.get("/animals/audit‐sample")
def audit_sample(db: Session = Depends(get_database)):
    """
    Return the first 10 raw AuditLog.payloads so you can see exactly
    what keys and nesting they have.
    """
    sample = db.query(AuditLog).limit(10).all()
    return { row.audit_id: row.payload for row in sample }
