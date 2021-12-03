from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()


class AccessEvent(Base):
    __tablename__ = "access_event"

    event = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, nullable=False)

    uid = Column(String, nullable=False)  # User ID
    cid = Column(String)  # Client ID
    sub = Column(String)  # User/subject name/email

    client_host = Column(String)  # Client host/IP

    path = Column(String)  # API path
    method = Column(String)  # API method
    body = Column(String)  # API request body


class PatientRecordEvent(Base):
    __tablename__ = "patient_record_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event = Column(Integer, ForeignKey("access_event.event"))

    pid = Column(String, nullable=False)  # Patient ID

    resource = Column(String)  # Resource type (null if self)
    resource_id = Column(String)  # Resource ID if applicable

    # Resource operation
    operation = Column(String)


class MasterRecordEvent(Base):
    __tablename__ = "master_record_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event = Column(Integer, ForeignKey("access_event.event"))

    master_id = Column(Integer, nullable=False)  # Master Record ID

    # Resource operation
    operation = Column(String)


class PersonEvent(Base):
    __tablename__ = "person_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event = Column(Integer, ForeignKey("access_event.event"))

    person_id = Column(Integer, nullable=False)  # Person ID

    # Resource operation
    operation = Column(String)


class MessageEvent(Base):
    __tablename__ = "message_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event = Column(Integer, ForeignKey("access_event.event"))

    message_id = Column(Integer, nullable=False)  # Message ID

    # Resource operation
    operation = Column(String)
