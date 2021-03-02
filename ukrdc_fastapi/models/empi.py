"""Models which relate to the EMPI (JTRACE) Database"""
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

metadata = MetaData()
Base: Any = declarative_base(metadata=metadata)


class MasterRecord(Base):
    __tablename__ = "masterrecord"

    id = Column(Integer, primary_key=True)
    last_updated = Column("lastupdated", DateTime, nullable=False)
    date_of_birth = Column("dateofbirth", Date, nullable=False)
    gender = Column(String)
    givenname = Column(String)
    surname = Column(String)
    nationalid = Column(String, nullable=False)
    nationalid_type = Column("nationalidtype", String, nullable=False)
    status = Column(Integer, nullable=False)
    effective_date = Column("effectivedate", DateTime, nullable=False)
    creation_date = Column("creationdate", DateTime)

    link_records = relationship(
        "LinkRecord", backref="master_record", cascade="all, delete-orphan"
    )
    work_items = relationship(
        "WorkItem", backref="master_record", cascade="all, delete-orphan"
    )

    def __str__(self):
        return (
            f"MasterRecord({self.id}) <"
            f"{self.givenname} {self.surname} {self.date_of_birth} "
            f"{self.nationalid_type.strip()}:{self.nationalid}"
            f">"
        )

    def as_dict(self):
        return {
            "id": self.id,
            "last_updated": self.last_updated.isoformat(timespec="seconds"),
            "date_of_birth": self.date_of_birth.isoformat(),
            "gender": self.gender,
            "name": self.givenname,
            "surname": self.surname,
            "national_id": self.nationalid,
            "national_id_type": self.nationalid_type,
            "status": self.status,
            "effective_date": self.effective_date.isoformat(timespec="seconds"),
        }


class LinkRecord(Base):
    __tablename__ = "linkrecord"

    id = Column(Integer, primary_key=True)
    person_id = Column("personid", Integer, ForeignKey("person.id"), nullable=False)
    master_id = Column(
        "masterid", Integer, ForeignKey("masterrecord.id"), nullable=False
    )
    link_type = Column("linktype", Integer, nullable=False)
    link_code = Column("linkcode", Integer, nullable=False)
    link_desc = Column("linkdesc", String)
    updated_by = Column("updatedby", String)
    last_updated = Column("lastupdated", DateTime, nullable=False)

    def __str__(self):
        return f"LinkRecord({self.id}) <Person({self.person_id}), Master({self.master_id})>"

    def as_dict(self):
        return {"id": self.id, "person_id": self.person_id, "master_id": self.master_id}


class Person(Base):
    __tablename__ = "person"

    id = Column(Integer, primary_key=True)
    originator = Column(String, nullable=False)
    localid = Column(String, nullable=False)
    localid_type = Column("localidtype", String, nullable=False)
    nationalid = Column(String)
    nationalid_type = Column("nationalidtype", String)
    date_of_birth = Column("dateofbirth", Date, nullable=False)
    gender = Column(String, nullable=False)
    date_of_death = Column("dateofdeath", Date)
    givenname = Column(String)
    surname = Column(String)
    prev_surname = Column("prevsurname", String)
    other_given_names = Column("othergivennames", String)
    title = Column(String)
    postcode = Column(String)
    street = Column(String)
    std_surname = Column("stdsurname", String)
    std_prev_surname = Column("stdprevsurname", String)
    std_given_name = Column("stdgivenname", String)
    std_postcode = Column("stdpostcode", String)
    skip_duplicate_check = Column("skipduplicatecheck", Boolean)

    link_records = relationship(
        "LinkRecord", backref="person", cascade="all, delete-orphan"
    )
    work_items = relationship(
        "WorkItem", backref="person", cascade="all, delete-orphan"
    )
    xref_entries = relationship(
        "PidXRef", backref="person", cascade="all, delete-orphan"
    )

    def __str__(self):
        return (
            f"Person({self.id}) <"
            f"{self.givenname} {self.surname} {self.date_of_birth} "
            f"{self.localid_type.strip()}:{self.localid.strip()}"
            f">"
        )

    def as_dict(self, with_xref=True):
        data_dict = {
            "id": self.id,
            "originator": self.originator,
            "localid": self.localid,
            "localidType": self.localid_type,
            "dateOfBirth": self.date_of_birth,
            "gender": self.gender,
            "dateOfDeath": self.date_of_death,
            "name": self.givenname,
            "surname": self.surname,
        }

        if with_xref:
            data_dict["xref"] = [xref.as_dict() for xref in self.xref_entries]
        return data_dict


class WorkItem(Base):
    __tablename__ = "workitem"

    id = Column(Integer, primary_key=True)
    person_id = Column("personid", Integer, ForeignKey("person.id"), nullable=False)
    master_id = Column(
        "masterid", Integer, ForeignKey("masterrecord.id"), nullable=False
    )
    type = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    status = Column(Integer, nullable=False)
    last_updated = Column("lastupdated", DateTime, nullable=False)
    updated_by = Column("updatedby", String)
    update_description = Column("updatedesc", String)
    attributes = Column(String)

    def __str__(self):
        return f"WorkItem({self.id}) <{self.person_id}, {self.master_id}>"

    def as_dict(self):
        return {
            "id": self.id,
            "person_id": self.person_id,
            "master_id": self.master_id,
            "type": self.type,
            "description": self.description,
            "status": self.status,
            "person": self.person.as_dict(with_xref=True),
        }


class Audit(Base):
    __tablename__ = "audit"

    id = Column(Integer, primary_key=True)
    # Can't use relations here, otherwise on delete sqla would try to
    # set null for these fields and it would fail, because DB doesn't
    # allow nulls for these fields
    person_id = Column("personid", Integer, nullable=False)
    master_id = Column("masterid", Integer, nullable=False)
    type = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    main_nationalid = Column("mainnationalid", String)
    main_nationalid_type = Column("mainnationalidtype", String)
    last_updated = Column("lastupdated", DateTime, nullable=False)
    updated_by = Column("updatedby", String)

    def as_dict(self):
        return {
            "id": self.id,
            "person_id": self.person_id,
            "master_id": self.master_id,
            "type": self.type,
            "description": self.description,
            "status": self.status,
        }


class PidXRef(Base):
    __tablename__ = "pidxref"

    id = Column(Integer, primary_key=True)
    pid = Column(String, ForeignKey("person.localid"), nullable=False)
    sending_facility = Column("sendingfacility", String, nullable=False)
    sending_extract = Column("sendingextract", String, nullable=False)
    localid = Column(String, nullable=False)

    def __str__(self):
        return (
            f"PidXRef({self.id}) <"
            f"{self.pid} {self.sending_facility} {self.sending_extract} "
            f"{self.localid.strip()}"
            f">"
        )

    def as_dict(self):
        return {
            "id": self.id,
            "pid": self.pid,
            "sending_facility": self.sending_facility,
            "sending_extract": self.sending_extract,
            "localid": self.localid,
        }
