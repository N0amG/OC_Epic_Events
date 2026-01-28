from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    Enum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from epicevents.database import Base


class RoleEnum(PyEnum):
    """Énumération des rôles des collaborateurs"""

    MANAGEMENT = "management"  # Équipe de gestion
    SALES = "sales"  # Équipe commerciale
    SUPPORT = "support"  # Équipe support


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)

    # Relations (Pour naviguer facilement depuis le User)
    clients = relationship("Client", back_populates="sales_contact")
    events = relationship("Event", back_populates="support_contact")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)
    company_name = Column(String)
    creation_date = Column(DateTime, default=datetime.now)
    last_contact_date = Column(DateTime, default=datetime.now)

    # Clé étrangère : Un client appartient à un commercial (User)
    sales_contact_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relations
    sales_contact = relationship("User", back_populates="clients")
    contracts = relationship("Contract", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, full_name='{self.full_name}', company='{self.company_name}')>"


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    amount_due = Column(Numeric(10, 2), nullable=False)
    creation_date = Column(DateTime, default=datetime.now)
    is_signed = Column(Boolean, default=False)  # True = signé, False = brouillon

    # Clé étrangère : Un contrat appartient à un client
    client_id = Column(Integer, ForeignKey("clients.id"))

    # Relations
    client = relationship("Client", back_populates="contracts")
    events = relationship("Event", back_populates="contract")

    def __repr__(self):
        status = "signé" if self.is_signed else "brouillon"
        return f"<Contract(id={self.id}, total_amount={self.total_amount}, status='{status}')>"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_date_start = Column(DateTime)
    event_date_end = Column(DateTime)
    location = Column(String)
    attendees = Column(Integer)
    notes = Column(Text)

    # Clés étrangères
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    # L'événement est assigné à un membre du support (User)
    support_contact_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relations
    contract = relationship("Contract", back_populates="events")
    support_contact = relationship("User", back_populates="events")

    def __repr__(self):
        return f"<Event(id={self.id}, location='{self.location}', date='{self.event_date_start}')>"
