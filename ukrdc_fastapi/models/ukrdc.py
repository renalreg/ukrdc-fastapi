import sqlalchemy.orm.collections
import sqlalchemy.orm.dynamic
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

metadata = MetaData()
Base = declarative_base(metadata=metadata)

GLOBAL_LAZY = False


class PatientRecord(Base):
    __tablename__ = "patientrecord"

    pid = Column(String, primary_key=True)
    sendingfacility = Column(String)
    sendingextract = Column(String)
    localpatientid = Column(String)
    ukrdcid = Column(String)

    extract_time = Column("extracttime", DateTime)
    creation_date = Column("creation_date", DateTime)
    update_date = Column("update_date", DateTime)
    repository_creation_date = Column("repositorycreationdate", DateTime)
    repository_update_date = Column("repositoryupdatedate", DateTime)

    patient = relationship(
        "Patient", backref="record", uselist=False, cascade="all, delete-orphan"
    )
    lab_orders = relationship(
        "LabOrder", backref="record", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    social_histories = relationship("SocialHistory", cascade="all, delete-orphan")
    family_histories = relationship("FamilyHistory", cascade="all, delete-orphan")
    observations = relationship(
        "Observation", backref="record", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    allergies = relationship("Allergy", cascade="all, delete-orphan")
    diagnoses = relationship(
        "Diagnosis", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    cause_of_death = relationship(
        "CauseOfDeath", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    renaldiagnoses = relationship(
        "RenalDiagnosis", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    medications = relationship(
        "Medication", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )  # noqa
    dialysis_sessions = relationship(
        "DialysisSession", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    procedures = relationship("Procedure", cascade="all, delete-orphan")
    documents = relationship("Document", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")
    encounters = relationship("Encounter", cascade="all, delete-orphan")
    treatments = relationship(
        "Treatment", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    program_memberships = relationship(
        "ProgramMembership", cascade="all, delete-orphan"
    )
    transplants = relationship(
        "Transplant", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    opt_outs = relationship("OptOut", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")
    clinical_relationships = relationship(
        "ClinicalRelationship", cascade="all, delete-orphan"
    )

    surveys = relationship("Survey", cascade="all, delete-orphan")
    pvdata = relationship("PVData", uselist=False, cascade="all, delete-orphan")
    pvdelete = relationship("PVDelete", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")

    def __init__(
        self,
        pid="",
        sendingfacility="",
        sendingextract="",
        localpatientid="",
        ukrdcid="",
        lastupdated="",
        repository_creation_date="",
    ):
        if pid:
            self.pid = pid
        if sendingfacility:
            self.sendingfacility = sendingfacility
        if sendingextract:
            self.sendingextract = sendingextract
        if localpatientid:
            self.localpatientid = localpatientid
        if ukrdcid:
            self.ukrdcid = ukrdcid
        if repository_creation_date:
            self.repository_creation_date = repository_creation_date

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"UKRDCID:{self.ukrdcid} CREATED:{self.repository_creation_date}"
            f">"
        )


class Patient(Base):
    __tablename__ = "patient"

    pid = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)
    birth_time = Column("birthtime", Date)
    death_time = Column("deathtime", Date)
    gender = Column(String)
    country_of_birth = Column("countryofbirth", String)
    ethnic_group_code = Column("ethnicgroupcode", String)
    ethnic_group_description = Column("ethnicgroupdesc", String)
    person_to_contact_name = Column("persontocontactname", String)
    person_to_contact_number = Column("persontocontact_contactnumber", String)
    person_to_contact_relationship = Column("persontocontact_relationship", String)
    person_to_contact_number_comments = Column(
        "persontocontact_contactnumbercomments", String
    )
    person_to_contact_number_type = Column("persontocontact_contactnumbertype", String)
    occupation_code = Column("occupationcode", String)
    occupation_codestd = Column("occupationcodestd", String)
    occupation_description = Column("occupationdesc", String)
    primary_language = Column("primarylanguagecode", String)
    primary_language_codestd = Column("primarylanguagecodestd", String)
    primary_language_description = Column("primarylanguagedesc", String)
    dead = Column("death", Boolean)
    updated_on = Column("updatedon", DateTime)

    bloodgroup = Column(String)
    bloodrhesus = Column(String)

    dead = Column("death", Boolean)
    updated_on = Column("updatedon", DateTime)

    numbers = relationship(
        "PatientNumber",
        backref="patient",
        lazy=GLOBAL_LAZY,
        cascade="all, delete-orphan",
    )
    names = relationship("Name", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")
    contact_details = relationship(
        "ContactDetail", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    addresses = relationship("Address", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")
    familydoctor = relationship(
        "FamilyDoctor", uselist=False, cascade="all, delete-orphan"
    )

    def __init__(self, pid=None, birthtime=None, gender=None):
        if pid:
            self.pid = pid
        if birthtime:
            self.birth_time = birthtime
        if gender:
            self.gender = gender

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.birth_time}>"

    @property
    def name(self):
        """Return main patient name."""
        for name in self.names:
            if name.nameuse == "L":
                return name

    @property
    def first_ni_number(self):
        """Find the first nhs,chi or hsc number for a patient."""
        types = "NHS", "CHI", "HSC"
        for number in self.numbers:
            if number.numbertype == "NI" and number.organization in types:
                return number.patientid

    @property
    def first_hospital_number(self):
        """Find the first local hospital number for a patient."""
        hospital = "LOCALHOSP"
        for number in self.numbers:
            if number.numbertype == "MRN" and number.organization == hospital:
                return number.patientid


class CauseOfDeath(Base):
    __tablename__ = "causeofdeath"

    pid = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    diagnosis_type = Column("diagnosistype", String)

    diagnosing_clinician_code = Column("diagnosingcliniciancode", String)
    diagnosing_clinician_code_std = Column("diagnosingcliniciancodestd", String)
    diagnosing_clinician_desc = Column("diagnosingcliniciandesc", String)

    diagnosis_code = Column("diagnosiscode", String)
    diagnosis_code_std = Column("diagnosiscodestd", String)
    diagnosis_desc = Column("diagnosisdesc", String)

    comments = Column("comments", String)
    entered_on = Column("enteredon", DateTime)
    updated_on = Column("updatedon", DateTime)
    action_code = Column("actioncode", String)
    external_id = Column("externalid", String)


class FamilyDoctor(Base):
    __tablename__ = "familydoctor"

    id = Column(String, ForeignKey("patient.pid"), primary_key=True)
    gpname = Column(String)
    gpid = Column(String)
    gppracticeid = Column(String)
    addressuse = Column(String)
    fromtime = Column(DateTime)
    totime = Column(DateTime)
    street = Column(String)
    town = Column(String)
    county = Column(String)
    postcode = Column(String)
    countrycode = Column(String)
    countrycodestd = Column(String)
    countrydesc = Column(String)
    contactuse = Column(String)
    contactvalue = Column(String)
    email = Column(String)
    commenttext = Column(String)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.id}) <" f"{self.gpname} {self.gpid}" f">"
        )


class SocialHistory(Base):
    __tablename__ = "socialhistory"
    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))


class FamilyHistory(Base):
    __tablename__ = "familyhistory"
    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))


class Observation(Base):
    __tablename__ = "observation"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    idx = Column(Integer)
    observation_time = Column("observationtime", DateTime)
    observation_code = Column("observationcode", String)
    observation_code_std = Column("observationcodestd", String)
    observation_desc = Column("observationdesc", String)
    observation_value = Column("observationvalue", String)
    observation_units = Column("observationunits", String)
    comment_text = Column("commenttext", String)
    clinician_code = Column("cliniciancode", String)
    clinician_code_std = Column("cliniciancodestd", String)
    clinician_desc = Column("cliniciandesc", String)
    entered_at = Column("enteredatcode", String)
    entered_at_description = Column("enteredatdesc", String)
    entering_organization_code = Column("enteringorganizationcode", String)
    entering_organization_description = Column("enteringorganizationdesc", String)
    updated_on = Column("updatedon", DateTime)
    action_code = Column("actioncode", String)
    external_id = Column("externalid", String)
    pre_post = Column("prepost", String)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.observation_code} {self.observation_value}"
            f">"
        )


class OptOut(Base):
    __tablename__ = "optout"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    idx = Column(Integer)
    program_name = Column("programname", String)
    program_description = Column("programdescription", String)
    entered_by_code = Column("enteredbycode", String)
    entered_by_code_std = Column("enteredbycodestd", String)
    entered_by_desc = Column("enteredbydesc", String)
    entered_at_code = Column("enteredatcode", String)
    entered_at_code_std = Column("enteredatcodestd", String)
    entered_at_desc = Column("enteredatdesc", String)
    from_time = Column("fromtime", Date)
    to_time = Column("totime", Date)
    updated_on = Column("updatedon", DateTime)
    action_code = Column("actioncode", String)
    external_id = Column("externalid", String)


class Allergy(Base):
    __tablename__ = "allergy"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))


class Diagnosis(Base):
    __tablename__ = "diagnosis"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    diagnosis_code = Column("diagnosiscode", String)
    diagnosis_code_std = Column("diagnosiscodestd", String)
    diagnosis_desc = Column("diagnosisdesc", String)

    identification_time = Column("identificationtime", DateTime)
    onset_time = Column("onsettime", DateTime)

    comments = Column(String)


class RenalDiagnosis(Base):
    __tablename__ = "renaldiagnosis"

    pid = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    diagnosis_code = Column("diagnosiscode", String)
    diagnosis_code_std = Column("diagnosiscodestd", String)
    diagnosis_desc = Column("diagnosisdesc", String)

    identification_time = Column("identificationtime", DateTime)

    comments = Column(String)


class DialysisSession(Base):
    __tablename__ = "dialysissession"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    procedure_type_code = Column("proceduretypecode", String)
    procedure_type_code_std = Column("proceduretypecodestd", String)
    procedure_type_desc = Column("proceduretypedesc", String)

    procedure_time = Column("proceduretime", DateTime)

    qhd19 = Column(String)
    qhd20 = Column(String)
    qhd21 = Column(String)
    qhd22 = Column(String)
    qhd30 = Column(String)
    qhd31 = Column(String)
    qhd32 = Column(String)
    qhd33 = Column(String)


class Transplant(Base):

    __tablename__ = "transplant"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    procedure_type_code = Column("proceduretypecode", String)
    procedure_type_code_std = Column("proceduretypecodestd", String)
    procedure_type_desc = Column("proceduretypedesc", String)

    procedure_time = Column("proceduretime", DateTime)

    tra64 = Column(String)
    tra65 = Column(String)
    tra66 = Column(DateTime)
    tra69 = Column(DateTime)
    tra76 = Column(DateTime)
    tra77 = Column(String)
    tra78 = Column(String)
    tra79 = Column(String)
    tra8a = Column(String)
    tra81 = Column(String)
    tra82 = Column(String)
    tra83 = Column(String)
    tra84 = Column(String)
    tra85 = Column(String)


class Procedure(Base):
    __tablename__ = "procedure"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))


class Encounter(Base):
    __tablename__ = "encounter"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    from_time = Column("fromtime", DateTime)
    to_time = Column("totime", DateTime)


class ProgramMembership(Base):
    __tablename__ = "programmembership"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    program_name = Column("programname", String)
    from_time = Column("fromtime", Date)
    to_time = Column("totime", Date)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.program_name} {self.from_time}"
            f">"
        )


class ClinicalRelationship(Base):
    __tablename__ = "clinicalrelationship"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))


class Name(Base):
    __tablename__ = "name"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patient.pid"))
    nameuse = Column(String)
    prefix = Column(String)
    family = Column(String)
    given = Column(String)
    othergivennames = Column(String)
    suffix = Column(String)

    def __init__(self, id=None, pid=None, nameuse=None, family=None, given=None):
        if id:
            self.id = id
        if pid:
            self.pid = pid
        if nameuse:
            self.nameuse = nameuse
        if family:
            self.family = family
        if given:
            self.given = given

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.given} {self.family}"
            f">"
        )


class PatientNumber(Base):
    __tablename__ = "patientnumber"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patient.pid"))
    patientid = Column(String)
    organization = Column(String)
    numbertype = Column(String)

    def __init__(
        self, id=None, pid=None, number=None, organization=None, numbertype=None
    ):
        if id:
            self.id = id
        if pid:
            self.pid = pid
        if number:
            self.patientid = number
        if organization:
            self.organization = organization
        if numbertype:
            self.numbertype = numbertype

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.organization}:{self.numbertype}:{self.patientid}"
            ">"
        )


class Address(Base):
    __tablename__ = "address"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patient.pid"))
    addressuse = Column(String)
    from_time = Column("fromtime", Date)
    to_time = Column("totime", Date)
    street = Column(String)
    town = Column(String)
    county = Column(String)
    postcode = Column(String)
    country_code = Column("countrycode", String)
    country_description = Column("countrydesc", String)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.street} {self.town} {self.postcode}"
            f">"
        )


class ContactDetail(Base):
    __tablename__ = "contactdetail"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patient.pid"))
    use = Column("contactuse", String)
    value = Column("contactvalue", String)
    commenttext = Column(String)

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.use}:{self.value}>"


class Medication(Base):
    __tablename__ = "medication"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    idx = Column(Integer)
    # ...

    from_time = Column("fromtime", DateTime)
    to_time = Column("totime", DateTime)
    dose_uom_code = Column("doseuomcode", String)
    dose_uom_code_std = Column("doseuomcodestd", String)
    dose_uom_description = Column("doseuomdesc", String)
    dose_quantity = Column("dosequantity", String)
    drug_product_id_code = Column("drugproductidcode", String)
    drug_product_id_description = Column("drugproductiddesc", String)
    drug_product_generic = Column("drugproductgeneric", String)
    entering_organization_code = Column("enteringorganizationcode", String)
    entering_organization_description = Column("enteringorganizationdesc", String)
    frequency = Column(String)

    comment = Column("commenttext", String)

    route_code = Column("routecode", String)
    route_code_std = Column("routecodestd", String)
    route_desc = Column("routedesc", String)

    external_id = Column("externalid", String)

    updated_on = Column("updatedon", DateTime)

    repository_update_date = Column("repositoryupdatedate", DateTime)

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid})"


class Survey(Base):
    __tablename__ = "survey"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    surveytime = Column(DateTime)
    surveytypecode = Column(String)
    surveytypecodestd = Column(String)
    surveytypedesc = Column(String)
    enteredbycode = Column(String)
    enteredbycodestd = Column(String)
    enteredatcode = Column(String)
    enteredatcodestd = Column(String)
    enteredatdesc = Column(String)
    updatedon = Column(DateTime)
    externalid = Column(String)

    questions = relationship("Question", cascade="all, delete-orphan")
    scores = relationship("Score", cascade="all, delete-orphan")
    levels = relationship("Level", cascade="all, delete-orphan")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.surveytime}:{self.surveytypecode}"
            f">"
        )


class Question(Base):
    __tablename__ = "question"

    id = Column(String, primary_key=True)
    surveyid = Column(String, ForeignKey("survey.id"))

    questiontypecode = Column(String)
    questiontypecodestd = Column(String)
    questiontypedesc = Column(String)
    response = Column(String)


class Score(Base):
    __tablename__ = "score"

    id = Column(String, primary_key=True)
    surveyid = Column(String, ForeignKey("survey.id"))
    value = Column("scorevalue", String)
    scoretypecode = Column(String)
    scoretypecodestd = Column(String)
    scoretypedesc = Column(String)


class Level(Base):
    __tablename__ = "level"

    id = Column(String, primary_key=True)
    surveyid = Column(String, ForeignKey("survey.id"))
    value = Column("levelvalue", String)
    leveltypecode = Column(String)
    leveltypecodestd = Column(String)
    leveltypedesc = Column(String)


class Document(Base):
    __tablename__ = "document"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    idx = Column(Integer)
    documenttime = Column(DateTime)
    notetext = Column(String)
    documenttypecode = Column(String)
    documenttypecodestd = Column(String)
    documenttypedesc = Column(String)

    cliniciancode = Column(String)
    cliniciancodestd = Column(String)
    cliniciandesc = Column(String)
    documentname = Column(String)
    statuscode = Column(String)
    statuscodestd = Column(String)
    statusdesc = Column(String)
    enteredbycode = Column(String)
    enteredbycodestd = Column(String)
    enteredbydesc = Column(String)
    enteredatcode = Column(String)
    enteredatcodestd = Column(String)
    enteredatdesc = Column(String)
    filetype = Column(String)
    filename = Column(String)
    stream = Column(LargeBinary)
    documenturl = Column(String)
    updatedon = Column(DateTime)
    actioncode = Column(String)
    externalid = Column(String)

    update_date = Column(DateTime)
    creation_date = Column(DateTime)

    repository_update_date = Column("repositoryupdatedate", DateTime)

    def __init__(
        self,
        id=None,
        pid=None,
        idx=None,
        documenttime=None,
        notetext=None,
        docname=None,
    ):
        if id:
            self.id = id
        if pid:
            self.pid = pid
        if idx:
            self.idx = idx
        if documenttime:
            self.documenttime = documenttime
        if notetext:
            self.notetext = notetext
        if docname:
            self.documentname = docname


class LabOrder(Base):
    __tablename__ = "laborder"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    receiving_location = Column("receivinglocationcode", String)
    receiving_location_description = Column("receivinglocationdesc", String)
    placer_id = Column("placerid", String)
    filler_id = Column("fillerid", String)
    ordered_by = Column("orderedbycode", String)
    ordered_by_description = Column("orderedbydesc", String)
    order_item = Column("orderitemcode", String)
    order_item_description = Column("orderitemdesc", String)
    order_category = Column("ordercategorycode", String)
    order_category_description = Column("ordercategorydesc", String)
    specimen_collected_time = Column("specimencollectedtime", DateTime)
    specimen_received_time = Column("specimenreceivedtime", DateTime)
    status = Column("status", String)
    priority = Column("prioritycode", String)
    priority_description = Column("prioritydesc", String)
    specimen_source = Column("specimensource", String)
    duration = Column("duration", String)
    patient_class = Column("patientclasscode", String)
    patient_class_description = Column("patientclassdesc", String)
    entered_on = Column("enteredon", DateTime)
    entered_at = Column("enteredatcode", String)
    entered_at_description = Column("enteredatdesc", String)
    external_id = Column("externalid", String)
    entering_organization_code = Column("enteringorganizationcode", String)
    entering_organization_description = Column("enteringorganizationdesc", String)

    result_items = relationship(
        "ResultItem", lazy=GLOBAL_LAZY, backref="order", cascade="all, delete-orphan"
    )


class ResultItem(Base):
    __tablename__ = "resultitem"

    id = Column(String, primary_key=True)
    order_id = Column("orderid", String, ForeignKey("laborder.id"))

    result_type = Column("resulttype", String)
    entered_on = Column("enteredon", DateTime)
    pre_post = Column("prepost", String)
    service_id = Column("serviceidcode", String)
    service_id_std = Column("serviceidcodestd", String)
    service_id_description = Column("serviceiddesc", String)
    sub_id = Column("subid", String)
    value = Column("resultvalue", String)
    value_units = Column("resultvalueunits", String)
    reference_range = Column("referencerange", String)
    interpretation_codes = Column("interpretationcodes", String)
    status = Column(String)
    observation_time = Column("observationtime", DateTime)
    comments = Column("commenttext", String)
    reference_comment = Column("referencecomment", String)


class PVData(Base):
    __tablename__ = "pvdata"

    id = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)
    rrtstatus = Column(String)
    tpstatus = Column(String)
    diagnosisdate = Column(Date)
    bloodgroup = Column(String)
    update_date = Column(DateTime)
    creation_date = Column(DateTime)

    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"

    def __init__(self, id=None):
        if id:
            self.id = id


class PVDelete(Base):
    __tablename__ = "pvdelete"

    did = Column(Integer, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    observation_time = Column("observationtime", DateTime)
    service_id = Column("serviceidcode", String)


class Treatment(Base):
    __tablename__ = "treatment"

    id = Column("id", String, primary_key=True)
    pid = Column("pid", String, ForeignKey("patientrecord.pid"))
    idx = Column("idx", Integer)

    encounter_number = Column("encounternumber", String)
    encounter_type = Column("encountertype", String)

    from_time = Column("fromtime", DateTime)
    to_time = Column("totime", DateTime)

    admitting_clinician_code = Column("admittingcliniciancode", String)
    admitting_clinician_code_std = Column("admittingcliniciancodestd", String)
    admitting_clinician_desc = Column("admittingcliniciandesc", String)

    admit_reason_code = Column("admitreasoncode", String)
    admit_reason_code_std = Column("admitreasoncodestd", String)
    admit_reason_description = Column("admitreasondesc", String)

    admission_source_code = Column("admissionsourcecode", String)
    admission_source_code_std = Column("admissionsourcecodestd", String)
    admission_source_desc = Column("admissionsourcedesc", String)

    discharge_reason_code = Column("dischargereasoncode", String)
    discharge_reason_code_std = Column("dischargereasoncodestd", String)
    discharge_reason_desc = Column("dischargereasondesc", String)

    discharge_location_code = Column("dischargelocationcode", String)
    discharge_location_code_std = Column("dischargelocationcodestd", String)
    discharge_location_desc = Column("dischargelocationdesc", String)

    health_care_facility_code = Column("healthcarefacilitycode", String)
    health_care_facility_code_std = Column("healthcarefacilitycodestd", String)
    health_care_facilit_desc = Column("healthcarefacilitydesc", String)

    entered_at_code = Column("enteredatcode", String)

    visit_description = Column("visitdescription", String)
    updated_on = Column("updatedon", DateTime)
    action_code = Column("actioncode", String)
    external_id = Column("externalid", String)

    hdp01 = Column("hdp01", String)
    hdp02 = Column("hdp02", String)
    hdp03 = Column("hdp03", String)
    hdp04 = Column("hdp04", String)
    qbl05 = Column("qbl05", String)
    qbl06 = Column("qbl06", String)
    qbl07 = Column("qbl07", String)
    erf61 = Column("erf61", String)
    pat35 = Column("pat35", String)
