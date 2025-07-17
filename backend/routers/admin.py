# backend/routers/admin.py
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date

from backend import models, database
from backend.database import get_database
from backend.hedera_client import publish_and_audit
from backend.models import Animal, Event
from backend.schemas import EventOut

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post(
    "/animal_onboarding",
    response_model=EventOut,
    summary="Create a new animal and add its onboarding event to the chain",
)
def animal_onboarding(
    tag_id: str         = Form(..., description="The tag or chip ID"),
    farm_id: int        = Form(..., description="ID of the farm this animal belongs to"),
    performed_by: int        = Form(...),
    breed: str          = Form(..., description="Animal breed"),
    sex: str            = Form(..., description="Male or Female"),
    date_of_birth: date = Form(..., description="Date of birth (YYYY‑MM‑DD)"),
    status: str         = Form(..., description="Active or Inactive"),
    db: Session         = Depends(get_database),
):
    # make sure the tag is unique
    existing = db.query(Animal).filter_by(tag_id=tag_id).first()
    if existing:
        raise HTTPException(400, f"Tag {tag_id!r} is already in use.")

    # create Animal record
    animal = models.Animal(tag_id=tag_id, farm_id=farm_id, breed=breed)
    database.add(animal); database.flush();

    # log Event
    event = models.Event(
        animal_id   = animal.animal_id,
        event_type  = "animal registration",
        performed_by= performed_by,
        details     = {"tag_id": tag_id,
                        "breed": breed,
                       "sex": sex,
                       "date of birth": date_of_birth,
                       "status": status,},
    )
    database.add(event); database.commit(); database.refresh(event)

    # publish to HCS
    payload = {
      "eventId":      event.event_id,
      "animalId":     animal.animal_id,
      "eventType":    event.event_type,
      "performedBy":  performed_by,
      "details":      event.details,
      "timestamp":    datetime.utcnow().isoformat() + "Z"
    }
    publish_and_audit(payload, database)

    return event