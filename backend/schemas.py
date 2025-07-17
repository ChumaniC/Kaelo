from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, Union


class EventCreate(BaseModel):
    animal_id: int
    event_type: str
    performed_by: int
    details: Union[Dict[str, Any], str]

class EventOut(EventCreate):
    event_id: int
    event_time: datetime
    created_at: datetime

    class EventBase(BaseModel):
        animal_id: int
        event_type: str
        performed_by: int
        details: Any

class AuditEntry(BaseModel):
    event_id: int
    event_type: str
    consensus_timestamp: datetime
    hcs_transaction_id: str
    payload: Dict[str, Any]

    class Config:
        orm_mode = True