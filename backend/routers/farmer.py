# backend/routers/farmer.py
from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.orm import Session
from datetime import datetime
from backend import models, schemas
from backend.database import get_database
from backend.hedera_client import publish_and_audit

router = APIRouter(prefix="/farmer", tags=["farmer"])

@router.post("/animal-registration", response_model=schemas.EventOut)
def register_animal(
    tag_id:        str = Form(...),
    breed:         str = Form(...),
    farm_id:       int = Form(...),
    performed_by:  int = Form(...),        # farmer’s user ID - but this will be linked to the current session of the current farmer logged in
    db:            Session = Depends(get_database),
):
    # 1) create Animal record
    animal = models.Animal(tag_id=tag_id, farm_id=farm_id, breed=breed)
    db.add(animal); db.commit(); db.refresh(animal)

    # 2) log Event
    evt = models.Event(
        animal_id   = animal.animal_id,
        event_type  = "animal registration",
        performed_by= performed_by,
        details     = {"breed": breed},
    )
    db.add(evt); db.commit(); db.refresh(evt)

    # 3) publish to HCS
    payload = {
      "eventId":      evt.event_id,
      "animalId":     animal.animal_id,
      "eventType":    evt.event_type,
      "performedBy":  performed_by,
      "details":      evt.details,
      "timestamp":    datetime.utcnow().isoformat() + "Z"
    }
    publish_and_audit(payload, db)

    return evt

@router.post("/breeding", response_model=schemas.EventOut)
def record_breeding(
    animal_id:     int = Form(...),
    performed_by:  int = Form(...),
    notes:         str = Form(None),
    db:            Session = Depends(get_database),
):
    evt = models.Event(
        animal_id   = animal_id,
        event_type  = "breeding",
        performed_by= performed_by,
        details     = {"notes": notes or ""},
    )
    db.add(evt); db.commit(); db.refresh(evt)

    publish_and_audit({
      "eventId":     evt.event_id,
      "animalId":    animal_id,
      "eventType":   "breeding",
      "performedBy": performed_by,
      "details":     evt.details,
      "timestamp":   datetime.utcnow().isoformat() + "Z"
    }, db)
    return evt

@router.post("/gestation", response_model=schemas.EventOut)
def record_gestation(
    animal_id:     int     = Form(...),
    performed_by:  int     = Form(...),
    expected_date: str     = Form(...),  # e.g. "2025-10-01"
    notes:         str     = Form(None),
    db:            Session = Depends(get_database),
):
    """
    Record a gestation (pregnancy check) event.
    """
    # 1) Create the Event
    evt = models.Event(
        animal_id   = animal_id,
        event_type  = "gestation",
        performed_by= performed_by,
        details     = {
            "expected_date": expected_date,
            "notes": notes or ""
        },
    )
    db.add(evt); db.commit(); db.refresh(evt)

    # 2) Publish on-chain
    payload = {
      "eventId":      evt.event_id,
      "animalId":     animal_id,
      "eventType":    "gestation",
      "performedBy":  performed_by,
      "details":      evt.details,
      "timestamp":    datetime.utcnow().isoformat() + "Z"
    }
    publish_and_audit(payload, db)

    return evt


@router.post("/birth-registration", response_model=schemas.EventOut)
def record_birth(
    animal_id:    int = Form(...),
    performed_by: int = Form(...),
    birth_weight: float = Form(None),
    db:           Session = Depends(get_database),
):
    evt = models.Event(
        animal_id   = animal_id,
        event_type  = "birth_registration",
        performed_by= performed_by,
        details     = {"birth_weight": birth_weight},
    )
    db.add(evt); db.commit(); db.refresh(evt)
    publish_and_audit({
      "eventId":     evt.event_id,
      "animalId":    animal_id,
      "eventType":   "birth_registration",
      "performedBy": performed_by,
      "details":     evt.details,
      "timestamp":   datetime.utcnow().isoformat() + "Z"
    }, db)
    return evt

@router.post("/weigh-in", response_model=schemas.EventOut)
def record_weigh_in(
    animal_id:    int = Form(...),
    performed_by: int = Form(...),
    weight:       float = Form(...),
    db:           Session = Depends(get_database),
):
    evt = models.Event(
        animal_id   = animal_id,
        event_type  = "weigh_in",
        performed_by= performed_by,
        details     = {"weight": weight},
    )
    db.add(evt); db.commit(); db.refresh(evt)
    publish_and_audit({
      "eventId":     evt.event_id,
      "animalId":    animal_id,
      "eventType":   "weigh_in",
      "performedBy": performed_by,
      "details":     evt.details,
      "timestamp":   datetime.utcnow().isoformat() + "Z"
    }, db)
    return evt

@router.post("/misc", response_model=schemas.EventOut)
def record_misc(
    animal_id:    int = Form(...),
    performed_by: int = Form(...),
    description:  str = Form(...),
    db:           Session = Depends(get_database),
):
    evt = models.Event(
        animal_id   = animal_id,
        event_type  = "miscellaneous",
        performed_by= performed_by,
        details     = {"description": description},
    )
    db.add(evt); db.commit(); db.refresh(evt)
    publish_and_audit({
      "eventId":     evt.event_id,
      "animalId":    animal_id,
      "eventType":   "miscellaneous",
      "performedBy": performed_by,
      "details":     evt.details,
      "timestamp":   datetime.utcnow().isoformat() + "Z"
    }, db)
    return evt
