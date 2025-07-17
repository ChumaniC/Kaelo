import enum
from tkinter import CHAR

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Date, DECIMAL, Text, Numeric, Enum, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base

class Event(Base):
    __tablename__ = "events"
    event_id      = Column(Integer, primary_key=True, index=True)
    animal_id     = Column(Integer, nullable=False)
    event_type    = Column(String, nullable=False)
    event_time    = Column(DateTime(timezone=True), server_default=func.now())
    performed_by  = Column(Integer, nullable=False)             # references users.user_id
    details       = Column(JSON, nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    audit_logs = relationship("AuditLog", back_populates="event")

class AuditLog(Base):
    __tablename__ = "audit_log"
    audit_id            = Column(Integer, primary_key=True, index=True)
    event_id  = Column(Integer, ForeignKey("events.event_id"), nullable=False)
    hcs_transaction_id  = Column(String, nullable=False)
    consensus_timestamp = Column(DateTime(timezone=True), nullable=False)
    payload             = Column(JSON, nullable=False)
    ingested_at         = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", backref="audit_entries")

    @property
    def event_type(self) -> str:
        return self.event.event_type

class Role(Base):
    __tablename__ = "roles"
    role_id    = Column(Integer, primary_key=True, index=True)
    name       = Column(String(50), nullable=False, unique=True)   # e.g. 'farmer','vet','regulator','buyer'
    description= Column(String(255))


class User(Base):
    __tablename__ = "users"
    user_id       = Column(Integer, primary_key=True, index=True)
    username      = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(100), nullable=False)
    email         = Column(String(100), unique=True)
    role_id       = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Farm(Base):
    __tablename__ = "farms"
    farm_id    = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100))
    location   = Column(Text)
    owner_id   = Column(Integer, ForeignKey("users.user_id"), nullable=False)  # must be a ‘farmer’
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Animal(Base):
    __tablename__ = "animals"
    animal_id     = Column(Integer, primary_key=True, index=True)
    tag_id        = Column(String(50), nullable=False, unique=True)  # RFID or QR code
    farm_id       = Column(Integer, ForeignKey("farms.farm_id"), nullable=False)
    breed         = Column(String(50))
    sex           = Column(String(10))
    date_of_birth = Column(Date)
    status        = Column(String(20), nullable=False, default="active")  # active, sold, deceased
    created_at    = Column(DateTime(timezone=True), server_default=func.now())


class VetVisit(Base):
    __tablename__ = "vet_visits"
    vet_visit_id   = Column(Integer, primary_key=True, index=True)
    event_id       = Column(Integer, ForeignKey("events.event_id"), nullable=False)
    performed_by      = Column(Integer)
    treatment      = Column(String(100))
    dosage         = Column(String(50))
    weight      = Column(Float)
    notes         = Column(String(500))
    cost           = Column(DECIMAL(10, 2))
    next_visit_date= Column(Date)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())


class FeedLog(Base):
    __tablename__ = "feed_logs"
    feed_log_id  = Column(Integer, primary_key=True, index=True)
    event_id     = Column(Integer, ForeignKey("events.event_id"), nullable=False)
    feed_type    = Column(String(50))
    quantity     = Column(DECIMAL(10, 2))    # e.g. kg
    cost         = Column(DECIMAL(10, 2))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


class OffspringPurposeEnum(str, enum.Enum):
        Dairy = "Dairy"
        Meat = "Meat"
        Wool = "Wool"
        Draft = "Draft"
        Layer = "Layer"
        Broiler = "Broiler"
        Other = "Other"


class OwnershipTransfer(Base):
    __tablename__ = "ownership_transfers"
    transfer_id  = Column(Integer, primary_key=True, index=True)
    event_id     = Column(Integer, ForeignKey("events.event_id"), nullable=False)
    from_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    to_user_id   = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    sale_price   = Column(DECIMAL(10, 2))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


class BirthRegistration(Base):
    __tablename__ = "birth_registrations"

    birth_registration_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    event_id = Column(
        Integer,
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    mother_animal_id = Column(
        Integer,
        ForeignKey("animals.animal_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    registration_date = Column(
        Date,
        nullable=False
    )

    mother_weight = Column(
        Numeric(8, 2),
        nullable=True
    )

    sex = Column(String(10), nullable=True)

    offspring_breed = Column(
        String(50),
        nullable=True
    )

    offspring_purpose = Column(
        Enum(OffspringPurposeEnum, name="offspring_purpose_enum"),
        nullable=True
    )

    offspring_weight = Column(
        Numeric(8, 2),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )