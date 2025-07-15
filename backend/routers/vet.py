# backend/routers/vet.py
from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from datetime import datetime
from backend.database import get_database
from backend.hedera_client import publish_and_audit
from backend.schemas import EventOut
from backend.models import Event
router = APIRouter(prefix="/vet", tags=["vet"])

@router.post("/vet-visit", response_model=EventOut)
def vet_visit(
    animal_id:      int   = Form(...),
    performed_by:   int   = Form(...),
    notes:          str   = Form(None),
    db:             Session = Depends(get_database),
):
    evt = Event(
        animal_id   = animal_id,
        event_type  = "vet_visit",
        performed_by= performed_by,
        details     = {"notes": notes or ""},
    )
    db.add(evt); db.commit(); db.refresh(evt)
    publish_and_audit({
      "eventId":     evt.event_id,
      "animalId":    animal_id,
      "eventType":   "vet_visit",
      "performedBy": performed_by,
      "details":     evt.details,
      "timestamp":   datetime.utcnow().isoformat() + "Z"
    }, db)
    return evt

@router.post("/vaccination", response_model=EventOut)
def vaccination(
    animal_id:      int    = Form(...),
    performed_by:   int    = Form(...),
    vaccine_type:   str    = Form(...),
    dose:           str    = Form(...),
    db:             Session = Depends(get_database),
):
    evt = Event(
        animal_id   = animal_id,
        event_type  = "vaccination",
        performed_by= performed_by,
        details     = {"vaccine_type": vaccine_type, "dose": dose},
    )
    db.add(evt); db.commit(); db.refresh(evt)
    publish_and_audit({
      "eventId":       evt.event_id,
      "animalId":      animal_id,
      "eventType":     "vaccination",
      "performedBy":   performed_by,
      "details":       evt.details,
      "timestamp":     datetime.utcnow().isoformat() + "Z"
    }, db)
    return evt
