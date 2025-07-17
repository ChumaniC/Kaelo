# backend/routers/vet.py
from typing import Optional

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from datetime import datetime, date
from backend.database import get_database
from backend.hedera_client import publish_and_audit
from backend.schemas import EventOut
from backend.models import Event, VetVisit

router = APIRouter(prefix="/vet", tags=["vet"])

@router.post("/vet-visit", response_model=EventOut)
def vet_visit(
    animal_id:      int   = Form(...),
    performed_by:   int   = Form(...),
    notes:          str   = Form(None),
    database:             Session = Depends(get_database),
):
    event = Event(
        animal_id   = animal_id,
        event_type  = "vet_visit",
        performed_by= performed_by,
        details     = {"notes": notes or ""},
    )
    database.add(event); database.commit(); database.refresh(event)
    publish_and_audit({
      "eventId":     event.event_id,
      "animalId":    animal_id,
      "eventType":   "vet_visit",
      "performedBy": performed_by,
      "details":     event.details,
      "timestamp":   datetime.utcnow().isoformat() + "Z"
    }, database)
    return event

@router.post("/vaccination", response_model=EventOut)
def vaccination(
    animal_id:      int    = Form(...),
    performed_by:   int    = Form(...),
    vaccine_type:   str    = Form(...),
    cost:           int    = Form(...),
    dose:           str    = Form(...),
    weight:         float    = Form(...),
    next_visit_date: date = Form(...),
    notes:          Optional[str] = Form(None),
    database:             Session = Depends(get_database),
):
    event = Event(
        animal_id   = animal_id,
        event_type  = "vaccination",
        performed_by= performed_by,
        details     = {"vaccine_type": vaccine_type, "dose": dose,
                       "cost": cost, "weight": weight,
                       "next_visit_date": next_visit_date.isoformat() + "Z",
                       "notes": notes or ""},
    )
    database.add(event)
    database.flush()

    vetVisitEvent = VetVisit(
        event_id = event.event_id,
        treatment = event.details["vaccine_type"],
        dosage=event.details["dose"],
        weight=event.details["weight"],
        next_visit_date = event.details["next_visit_date"],
        notes = event.details["notes"],
        performed_by = performed_by
    )
    database.add(vetVisitEvent)
    database.commit()
    database.refresh(vetVisitEvent)

    publish_and_audit({
      "eventId":       event.event_id,
      "animalId":      animal_id,
      "eventType":     "vaccination",
      "performedBy":   performed_by,
      "details":       event.details,
      "timestamp":     datetime.utcnow().isoformat() + "Z"
    }, database)
    return event
