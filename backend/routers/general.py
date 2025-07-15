# backend/routers/general.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_database
from backend.schemas import EventOut
from backend.models import Event, Animal

router = APIRouter(prefix="/general", tags=["general"])

@router.get("/animals/{tag_id}/history", response_model=List[EventOut])
def view_history(tag_id: str, db: Session = Depends(get_database)):
    # find the animal
    animal = db.query(Animal).filter_by(tag_id=tag_id).first()
    if not animal:
        raise HTTPException(404, f"Animal {tag_id} not found")

    # fetch all events for that animal
    events = (
        db.query(Event)
          .filter_by(animal_id=animal.animal_id)
          .order_by(Event.event_time)
          .all()
    )
    return events
