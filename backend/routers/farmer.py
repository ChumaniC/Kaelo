# backend/routers/farmer.py
from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.orm import Session
from datetime import datetime, date
from backend import models, schemas
from backend.database import get_database
from backend.hedera_client import publish_and_audit
from backend.models import OffspringPurposeEnum, Animal, Event, BirthRegistration

router = APIRouter(prefix="/farmer", tags=["farmer"])

@router.post("/animal-registration", response_model=schemas.EventOut)
def register_animal(
    tag_id:        str = Form(...),
    breed:         str = Form(...),
    farm_id:       int = Form(...),
    performed_by:  int = Form(...),        # farmer’s user ID - but this will be linked to the current session of the current farmer logged in
    database:            Session = Depends(get_database),
):
    # create Animal record
    animal = models.Animal(tag_id=tag_id, farm_id=farm_id, breed=breed)
    database.add(animal); database.commit(); database.refresh(animal)

    # log Event
    event = models.Event(
        animal_id   = animal.animal_id,
        event_type  = "animal registration",
        performed_by= performed_by,
        details     = {"breed": breed},
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

@router.post("/breeding", response_model=schemas.EventOut)
def record_breeding(
    animal_id:     int = Form(...),
    performed_by:  int = Form(...),
    notes:         str = Form(None),
    database:            Session = Depends(get_database),
):
    event = models.Event(
        animal_id   = animal_id,
        event_type  = "breeding",
        performed_by= performed_by,
        details     = {"notes": notes or ""},
    )
    database.add(event); database.commit(); database.refresh(event)

    publish_and_audit({
      "eventId":     event.event_id,
      "animalId":    animal_id,
      "eventType":   "breeding",
      "performedBy": performed_by,
      "details":     event.details,
      "timestamp":   datetime.utcnow().isoformat() + "Z"
    }, database)
    return event

@router.post("/gestation", response_model=schemas.EventOut)
def record_gestation(
    animal_id:     int     = Form(...),
    performed_by:  int     = Form(...),
    expected_date: str     = Form(...),  # e.g. "2025-10-01"
    notes:         str     = Form(None),
    database:            Session = Depends(get_database),
):
    """
    Record a gestation (pregnancy check) event.
    """
    # Create the Event
    event = models.Event(
        animal_id   = animal_id,
        event_type  = "gestation",
        performed_by= performed_by,
        details     = {
            "expected_date": expected_date,
            "notes": notes or ""
        },
    )
    database.add(event); database.commit(); database.refresh(event)

    # Publish on-chain
    payload = {
      "eventId":      event.event_id,
      "animalId":     animal_id,
      "eventType":    "gestation",
      "performedBy":  performed_by,
      "details":      event.details,
      "timestamp":    datetime.utcnow().isoformat() + "Z"
    }
    publish_and_audit(payload, database)

    return event


@router.post("/birth-registration", response_model=schemas.EventOut)
def record_birth_registration(
        mother_animal_id: int = Form(...),
        performed_by: int = Form(...),
        registration_date: date = Form(...),
        mother_weight: float = Form(...),
        offspring_tag_id: str = Form(...),
        offspring_sex: str = Form(...),
        offspring_breed: str = Form(...),
        offspring_purpose: OffspringPurposeEnum = Form(...),
        offspring_weight: float = Form(...),
    database:                  Session = Depends(get_database),
):
    # Create the new Animal record for the calf,
    #    so it has its own animal_id we can reference later.
    mother = database.query(Animal).get(mother_animal_id)
    child = Animal(
        tag_id        = offspring_tag_id,
        farm_id       = mother.farm_id,
        breed         = offspring_breed,
        sex           = offspring_sex,
        date_of_birth = registration_date,
        status        = "active",
    )
    database.add(child)
    database.flush()   # populates child.animal_id

    # Create the generic Event row (so it shows up in your timeline)
    event = Event(
        animal_id    = mother_animal_id,
        event_type   = "birth_registration",
        performed_by = performed_by,
        details      = {
            "registrationDate": registration_date.isoformat(),
            "motherWeight":     mother_weight,
            "offspringAnimalId": child.animal_id
        },
    )
    database.add(event)
    database.flush()   # populates evt.event_id

    # Create the BirthRegistration‐specific row
    birth_registration = BirthRegistration(
        event_id           = event.event_id,
        mother_animal_id   = mother_animal_id,
        registration_date  = registration_date,
        mother_weight      = mother_weight,
        sex = offspring_sex,
        offspring_breed    = offspring_breed,
        offspring_purpose  = offspring_purpose,
        offspring_weight   = offspring_weight,
    )
    database.add(birth_registration)

    # commit all three at once
    database.commit()
    database.refresh(event)

    # 5) Publish *all* the details on Hedera
    payload = {
        "eventId":           event.event_id,
        "motherAnimalId":    mother_animal_id,
        "offspringAnimalId": child.animal_id,
        "offspringAnimalSex": child.sex,
        "eventType":         "birth_registration",
        "performedBy":       performed_by,
        "details": {
            "registrationDate": registration_date.isoformat(),
            "motherWeight":     mother_weight,
            "offspringBreed":   offspring_breed,
            "offspringPurpose": offspring_purpose.value,
            "offspringWeight":  offspring_weight,
        },
        "timestamp":         datetime.utcnow().isoformat() + "Z",
    }
    publish_and_audit(payload, database)
    return event

@router.post("/weigh-in", response_model=schemas.EventOut)
def record_weigh_in(
    animal_id:    int = Form(...),
    performed_by: int = Form(...),
    weight:       float = Form(...),
    database:           Session = Depends(get_database),
):
    event = models.Event(
        animal_id   = animal_id,
        event_type  = "weigh_in",
        performed_by= performed_by,
        details     = {"weight": weight},
    )
    database.add(event); database.commit(); database.refresh(event)
    publish_and_audit({
      "eventId":     event.event_id,
      "animalId":    animal_id,
      "eventType":   "weigh_in",
      "performedBy": performed_by,
      "details":     event.details,
      "timestamp":   datetime.utcnow().isoformat() + "Z"
    }, database)
    return event

@router.post("/misc", response_model=schemas.EventOut)
def record_misc(
    animal_id:    int = Form(...),
    performed_by: int = Form(...),
    description:  str = Form(...),
    database:           Session = Depends(get_database),
):
    event = models.Event(
        animal_id   = animal_id,
        event_type  = "miscellaneous",
        performed_by= performed_by,
        details     = {"description": description},
    )
    database.add(event); database.commit(); database.refresh(event)
    publish_and_audit({
      "eventId":     event.event_id,
      "animalId":    animal_id,
      "eventType":   "miscellaneous",
      "performedBy": performed_by,
      "details":     event.details,
      "timestamp":   datetime.utcnow().isoformat() + "Z"
    }, database)
    return event
