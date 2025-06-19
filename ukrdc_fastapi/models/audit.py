import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Integer, String, Column
from sqlalchemy.orm import (
    Mapped,
    relationship,
    mapped_column,
    DeclarativeBase,
)
from sqlalchemy.sql.schema import ForeignKey


class Base(DeclarativeBase):
    pass


class AccessEvent(Base):
    __tablename__ = "access_event"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    time:Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    uid:Mapped[str] = mapped_column(String, nullable=False)  # User ID
    cid:Mapped[Optional[str]] = mapped_column(String)  # Client ID
    sub:Mapped[Optional[str]] = mapped_column(String)  # User/subject name/email

    client_host:Mapped[Optional[str]] = mapped_column(String)  # Client host/IP

    path:Mapped[Optional[str]] = mapped_column(String)  # API path
    method:Mapped[Optional[str]] = mapped_column(String)  # API method
    body:Mapped[Optional[str]] = mapped_column(String)  # API request body

    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent", back_populates="access_event"
    )


class AuditEvent(Base):
    __tablename__ = "audit_event"

    id:Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id:Mapped[Optional[int]]  = mapped_column(Integer, ForeignKey("audit_event.id"))
    children: Mapped[list["AuditEvent"]] = relationship("AuditEvent")

    access_event_id:Mapped[Optional[int]]  = mapped_column(Integer, ForeignKey("access_event.id"))
    access_event: Mapped["AccessEvent"] = relationship(
        "AccessEvent", back_populates="audit_events"
    )

    resource:Mapped[Optional[int]]  = mapped_column(String)  # Resource type (null if self)
    resource_id:Mapped[Optional[str]] = mapped_column(String)  # Resource ID if applicable

    operation:Mapped[Optional[str]] = mapped_column(String)  # Resource operation
