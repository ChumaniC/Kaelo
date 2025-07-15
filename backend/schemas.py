from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict

class EventCreate(BaseModel):
    animal_id: int
    event_type: str
    performed_by: int
    details: Dict[str, Any]

class EventOut(EventCreate):
    event_id: int
    event_time: datetime
    created_at: datetime

    class EventBase(BaseModel):
        animal_id: int
        event_type: str
        performed_by: int
        details: Any
