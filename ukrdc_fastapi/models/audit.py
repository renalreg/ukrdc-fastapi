from typing import List

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship  # type: ignore
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()


class AccessEvent(Base):
    __tablename__ = "access_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, nullable=False)

    uid = Column(String, nullable=False)  # User ID
    cid = Column(String)  # Client ID
    sub = Column(String)  # User/subject name/email

    client_host = Column(String)  # Client host/IP

    path = Column(String)  # API path
    method = Column(String)  # API method
    body = Column(String)  # API request body

    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent", back_populates="access_event"
    )


class AuditEvent(Base):
    __tablename__ = "audit_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("audit_event.id"))
    children = relationship("AuditEvent")

    access_event_id = Column(Integer, ForeignKey("access_event.id"))
    access_event = relationship("AccessEvent", back_populates="audit_events")

    resource = Column(String)  # Resource type (null if self)
    resource_id = Column(String)  # Resource ID if applicable

    operation = Column(String)  # Resource operation
