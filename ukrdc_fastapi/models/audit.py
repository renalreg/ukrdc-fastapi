import datetime
from typing import List

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql.schema import ForeignKey


class Base(DeclarativeBase):
    pass


class AccessEvent(Base):
    __tablename__ = "access_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    uid: Mapped[str] = mapped_column(String, nullable=False)  # User ID
    cid: Mapped[str | None] = mapped_column(String)  # Client ID
    sub: Mapped[str | None] = mapped_column(String)  # User/subject name/email

    client_host: Mapped[str | None] = mapped_column(String)  # Client host/IP

    path: Mapped[str | None] = mapped_column(String)  # API path
    method: Mapped[str | None] = mapped_column(String)  # API method
    body: Mapped[str | None] = mapped_column(String)  # API request body

    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent", back_populates="access_event"
    )


class AuditEvent(Base):
    __tablename__ = "audit_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("audit_event.id"))
    children: Mapped[list["AuditEvent"]] = relationship("AuditEvent")

    access_event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("access_event.id")
    )
    access_event: Mapped["AccessEvent"] = relationship(
        "AccessEvent", back_populates="audit_events"
    )

    resource: Mapped[int | None] = mapped_column(String)  # Resource type (null if self)
    resource_id: Mapped[str | None] = mapped_column(String)  # Resource ID if applicable

    operation: Mapped[str | None] = mapped_column(String)  # Resource operation
