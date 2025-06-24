import re
import tempfile
from datetime import datetime
from pathlib import Path
import uuid

import fakeredis
import pytest
import pytest_asyncio
from fastapi import Security
from httpx import AsyncClient
from mirth_client import MirthAPI
from pytest_httpx import HTTPXMock
from pytest_postgresql import factories
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from ukrdc_sqla.empi import Base as JtraceBase
from ukrdc_sqla.empi import LinkRecord, WorkItem
from ukrdc_sqla.errorsdb import Base as ErrorsBase
from ukrdc_sqla.errorsdb import Channel, Latest
from ukrdc_sqla.errorsdb import Message as ErrorMessage
from ukrdc_sqla.stats import Base as StatsBase
from ukrdc_sqla.stats import ErrorHistory, MultipleUKRDCID
from ukrdc_sqla.ukrdc import Base as UKRDC3Base
from ukrdc_sqla.ukrdc import (
    Code,
    CodeExclusion,
    CodeMap,
    Document,
    LabOrder,
    Level,
    Medication,
    Observation,
    ProgramMembership,
    Question,
    ResultItem,
    Score,
    Survey,
    Treatment,
    DialysisSession,
    ModalityCodes,
    SatelliteMap,
)

from ukrdc_fastapi.dependencies import (
    auth,
    get_auditdb,
    get_errorsdb,
    get_jtrace,
    get_mirth,
    get_redis,
    get_root_task_tracker,
    get_statsdb,
    get_task_tracker,
    get_ukrdc3,
    get_usersdb,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.models.audit import Base as AuditBase
from ukrdc_fastapi.models.users import Base as UsersBase
from ukrdc_fastapi.utils.tasks import TaskTracker

from .utils import create_basic_facility, create_basic_patient, days_ago

# TODO: Move data creation into a submodule, and call data creation in each test rather than adding from conftest

# Using the factory to create a postgresql instance
socket_dir = tempfile.TemporaryDirectory()
postgresql_my_proc = factories.postgresql_proc(port=None, unixsocketdir=socket_dir.name)
postgresql_my = factories.postgresql("postgresql_my_proc")

MINIMAL_PDF_BYTES = (
    b"%PDF-1.0\n\n"
    + b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/+ MediaBox[0 0 3 3]>>endobj\n"
    + b"xref\n"
    + b"0 4\n"
    + b"0000000000 65535 f\n"
    + b"0000000010 00000 n\n"
    + b"0000000053 00000 n\n"
    + b"0000000102 00000 n\n"
    + b"trailer<</Size 4/Root 1 0 R>>\n"
    + b"startxref\n"
    + b"149\n"
    + b"%%EOF"
)

PID_1 = "PYTEST01:PV:00000000A"
PID_2 = "PYTEST02:PV:00000000A"
PID_3 = "PYTEST03:PV:00000000A"
PID_4 = "PYTEST04:PV:00000000A"
NI_1 = "888888888"
NI_2 = "888888887"
NI_3 = "888888886"
NI_4 = "888888885"
UKRDCID_1 = "999999999"
UKRDCID_2 = "999999911"
UKRDCID_3 = "999999922"
UKRDCID_4 = "999999933"


def populate_basic_stats(statsdb):
    row_1 = MultipleUKRDCID(
        group_id=1,
        master_id=1,
        last_updated=days_ago(0),
    )
    row_2 = MultipleUKRDCID(
        group_id=1,
        master_id=4,
        last_updated=days_ago(0),
    )
    statsdb.add(row_1)
    statsdb.add(row_2)
    statsdb.commit()


def populate_facilities_and_messages(ukrdc3, statsdb, errorsdb):
    create_basic_facility(
        "TSF01",
        "TSF01_DESCRIPTION",
        ukrdc3,
        pkb_in=False,
        pkb_out=True,
        pkb_msg_exclusions=None,
    )

    create_basic_facility(
        "TSF02",
        "TSF02_DESCRIPTION",
        ukrdc3,
        pkb_in=False,
        pkb_out=False,
        pkb_msg_exclusions=None,
    )

    channel_1 = Channel(
        id="00000000-0000-0000-0000-000000000000", name="MIRTH-CHANNEL-NAME-1"
    )
    channel_2 = Channel(
        id="00000000-0000-0000-0000-111111111111", name="MIRTH-CHANNEL-NAME-2"
    )
    errorsdb.add(channel_1)
    errorsdb.add(channel_2)

    facility_1_message_1 = ErrorMessage(
        id=1,
        message_id=1,
        channel_id="00000000-0000-0000-0000-000000000000",
        received=days_ago(2),
        msg_status="RECEIVED",
        ni=NI_1,
        filename="FILENAME_3.XML",
        facility="TSF01",
        error=None,
        status="STATUS3",
    )

    facility_1_message_2 = ErrorMessage(
        id=2,
        message_id=2,
        channel_id="00000000-0000-0000-0000-111111111111",
        received=days_ago(1),
        msg_status="ERROR",
        ni=NI_1,
        filename="FILENAME_1.XML",
        facility="TSF01",
        error="ERROR MESSAGE 1",
        status="STATUS1",
    )

    facility_1_ni_1_latest = Latest(facility="TSF01", ni=NI_1, message_id=2)

    facility_2_message_1 = ErrorMessage(
        id=3,
        message_id=3,
        channel_id="00000000-0000-0000-0000-000000000000",
        received=days_ago(730),
        msg_status="ERROR",
        ni=NI_2,
        filename="FILENAME_2.XML",
        facility="TSF02",
        error="ERROR MESSAGE 2",
        status="STATUS2",
    )
    facility_2_ni_2_latest = Latest(facility="TSF02", ni=NI_2, message_id=3)

    errorsdb.add(facility_1_message_1)
    errorsdb.add(facility_1_message_2)
    errorsdb.add(facility_1_ni_1_latest)

    errorsdb.add(facility_2_message_1)
    errorsdb.add(facility_2_ni_2_latest)

    errorsdb.commit()

    history_1 = ErrorHistory(facility="TSF01", date=days_ago(1), count=1)
    statsdb.add(history_1)

    statsdb.commit()


def populate_codes(ukrdc3):
    code3 = Code(
        coding_standard="CODING_STANDARD_1",
        code="CODE_1",
        description="DESCRIPTION_1",
        creation_date=days_ago(365),
    )
    code4 = Code(
        coding_standard="CODING_STANDARD_2",
        code="CODE_2",
        description="DESCRIPTION_2",
        creation_date=days_ago(365),
    )
    code5 = Code(
        coding_standard="CODING_STANDARD_2",
        code="CODE_3",
        description="DESCRIPTION_3",
        creation_date=days_ago(365),
    )
    code6 = Code(
        coding_standard="URTS_ETHNIC_GROUPING",
        code="eth1",
        description="DESCRIPTION_3",
        creation_date=days_ago(365),
    )
    code7 = Code(
        coding_standard="NHS_DATA_DICTIONARY",
        code="eth2",
        description="DESCRIPTION_3",
        creation_date=days_ago(365),
    )
    codemap1 = CodeMap(
        source_coding_standard="CODING_STANDARD_1",
        destination_coding_standard="CODING_STANDARD_2",
        source_code="CODE_1",
        destination_code="CODE_2",
        creation_date=days_ago(365),
    )
    codemap2 = CodeMap(
        source_coding_standard="CODING_STANDARD_2",
        destination_coding_standard="CODING_STANDARD_1",
        source_code="CODE_2",
        destination_code="CODE_1",
        creation_date=days_ago(365),
    )
    codemap3 = CodeMap(
        source_coding_standard="NHS_DATA_DICTIONARY",
        destination_coding_standard="URTS_ETHNIC_GROUPING",
        source_code="eth2",
        destination_code="eth1",
        creation_date=days_ago(365),
    )

    codeexc1 = CodeExclusion(
        coding_standard="CODING_STANDARD_1", code="CODE_1", system="SYSTEM_1"
    )
    codeexc2 = CodeExclusion(
        coding_standard="CODING_STANDARD_2", code="CODE_2", system="SYSTEM_1"
    )
    codeexc3 = CodeExclusion(
        coding_standard="CODING_STANDARD_2", code="CODE_2", system="SYSTEM_2"
    )

    code_eth_1 = Code(
        coding_standard="NHS_DATA_DICTIONARY",
        code="G",
        description="ETHNICITY_GROUP_DESCRIPTION",
        creation_date=days_ago(365),
    )

    ukrdc3.add(code3)
    ukrdc3.add(code4)
    ukrdc3.add(code5)
    ukrdc3.add(codemap1)
    ukrdc3.add(codemap2)
    ukrdc3.add(codeexc1)
    ukrdc3.add(codeexc2)
    ukrdc3.add(codeexc3)
    ukrdc3.add(code_eth_1)
    ukrdc3.add(code6)
    ukrdc3.add(code7)
    ukrdc3.add(codemap3)

    ukrdc3.commit()


def populate_patient_1_extra(session):
    membership_1 = ProgramMembership(
        id="MEMBERSHIP_1",
        pid=PID_1,
        programname="PROGRAM_NAME_1",
        fromtime=days_ago(365),
        totime=None,
    )
    membership_2 = ProgramMembership(
        id="MEMBERSHIP_2",
        pid=PID_1,
        programname="PROGRAM_NAME_2",
        fromtime=days_ago(365),
        totime=days_ago(1),
    )
    session.add(membership_1)
    session.add(membership_2)

    medication_1 = Medication(
        id="MEDICATION1",
        pid=PID_1,
        frequency="FREQUENCY",
        fromtime=days_ago(730),
        totime=None,
        drugproductgeneric="DRUG_PRODUCT_GENERIC",
        dosequantity=1,
        doseuomcode="DOSE_UOM_CODE",
        doseuomdesc="DOSE_UOM_DESCRIPTION",
        doseuomcodestd="DOSE_UOM_CODE_STD",
        repositoryupdatedate=datetime(2020, 3, 16),
    )
    medication_2 = Medication(
        id="MEDICATION2",
        pid=PID_1,
        frequency="FREQUENCY_2",
        fromtime=days_ago(730),
        totime=days_ago(-999),
        drugproductgeneric="DRUG_PRODUCT_GENERIC_2",
        dosequantity=2,
        doseuomcode="DOSE_UOM_CODE_2",
        doseuomdesc="DOSE_UOM_DESCRIPTION_2",
        doseuomcodestd="DOSE_UOM_CODE_STD_2",
        repositoryupdatedate=datetime(2020, 3, 16),
    )

    session.add(medication_1)
    session.add(medication_2)

    treatment_1 = Treatment(
        id="TREATMENT1",
        pid=PID_1,
        fromtime=days_ago(730),
        totime=None,
        admitreasoncode="1",
        admissionsourcecodestd="CF_RR7_TREATMENT",
        healthcarefacilitycode="TSF01",
        healthcarefacilitycodestd="ODS",
    )
    treatment_2 = Treatment(
        id="TREATMENT2",
        pid=PID_1,
        fromtime=days_ago(730),
        totime=days_ago(-999),
        admitreasoncode="1",
        admissionsourcecodestd="CF_RR7_TREATMENT",
        healthcarefacilitycode="TSF01",
        healthcarefacilitycodestd="ODS",
    )

    session.add(treatment_1)
    session.add(treatment_2)

    laborder_1 = LabOrder(
        id="LABORDER1",
        enteredatcode="TSF01",
        pid=PID_1,
        externalid="EXTERNAL_ID_1",
        ordercategorycode="ORDER_CATEGORY",
        specimencollectedtime=days_ago(365),
    )
    resultitem_1 = ResultItem(
        id="RESULTITEM1",
        order_id="LABORDER1",
        serviceidcodestd="SERVICE_ID_STD",
        serviceidcode="SERVICE_ID_1",
        serviceiddesc="SERVICE_ID_DESCRIPTION",
        resultvalue="VALUE",
        resultvalueunits="VALUE_UNITS",
        observationtime=days_ago(365),
        prepost="PRE",
    )
    laborder_2 = LabOrder(
        id="LABORDER2",
        enteredatcode="TSF02",
        pid=PID_1,
        externalid="EXTERNAL_ID_2",
        ordercategorycode="ORDER_CATEGORY",
        specimencollectedtime=days_ago(0),
    )
    resultitem_2 = ResultItem(
        id="RESULTITEM2",
        order_id="LABORDER2",
        serviceidcodestd="SERVICE_ID_STD",
        serviceidcode="SERVICE_ID_2",
        serviceiddesc="SERVICE_ID_DESCRIPTION",
        resultvalue="VALUE",
        resultvalueunits="VALUE_UNITS",
        observationtime=days_ago(0),
    )
    session.add(laborder_1)
    session.add(resultitem_1)
    session.add(laborder_2)
    session.add(resultitem_2)

    observation_1 = Observation(
        id="OBSERVATION1",
        pid=PID_1,
        observationcodestd="OBSERVATION_CODE_STD",
        observationcode="OBSERVATION_CODE",
        observationdesc="OBSERVATION_DESC",
        observationvalue="OBSERVATION_VALUE",
        observationunits="OBSERVATION_UNITS",
        observationtime=days_ago(365),
        prepost="PRE",
    )

    session.add(observation_1)

    observation_dia = Observation(
        id="OBSERVATION_DIA_1",
        pid=PID_1,
        observationcodestd="PV",
        observationcode="bpdia",
        observationdesc="OBSERVATION_DIA_1_DESC",
        observationvalue="OBSERVATION_DIA_1_VALUE",
        observationunits="OBSERVATION_DIA_1_UNITS",
        observationtime=days_ago(730),
    )
    observation_sys = Observation(
        id="OBSERVATION_SYS_1",
        pid=PID_1,
        observationcodestd="PV",
        observationcode="bpsys",
        observationdesc="OBSERVATION_SYS_1_DESC",
        observationvalue="OBSERVATION_SYS_1_VALUE",
        observationunits="OBSERVATION_SYS_1_UNITS",
        observationtime=days_ago(730),
    )
    session.add(observation_dia)
    session.add(observation_sys)

    dia_session_1 = DialysisSession(
        id="DIA_SESSION_1",
        pid=PID_1,
        proceduretypecode="302497006",
        proceduretypecodestd="SNOMED",
        proceduretypedesc="Haemodialysis",
        proceduretime=days_ago(1),
        enteredbycode="user1",
        enteredbycodestd="LOCAL",
        enteredbydesc="User 1 Name",
        enteredatcode="TSF01",
        externalid=str(uuid.uuid4()),
        qhd19="N",
        qhd20="AVF",
        qhd21="BB",
        qhd22="N",
        qhd30="300",
        qhd31="150",
        qhd32="140",
        qhd33="U",
    )
    dia_session_2 = DialysisSession(
        id="DIA_SESSION_2",
        pid=PID_1,
        proceduretypecode="PX",
        proceduretypecodestd="RR35",
        proceduretypedesc="Plasma Exchange",
        proceduretime=days_ago(2),
        enteredbycode="user1",
        enteredbycodestd="LOCAL",
        enteredbydesc="User 1 Name",
        enteredatcode="TSF01",
        externalid=str(uuid.uuid4()),
        qhd19="N",
        qhd20="AVF",
        qhd21="BB",
        qhd22="N",
        qhd30="300",
        qhd31="150",
        qhd32="140",
        qhd33="U",
    )
    session.add(dia_session_1)
    session.add(dia_session_2)

    survey_1 = Survey(
        id="SURVEY1",
        pid=PID_1,
        surveytime=days_ago(730),
        surveytypecode="TYPECODE",
        enteredbycode="ENTEREDBYCODE",
        enteredatcode="ENTEREDATCODE",
    )

    question_1 = Question(
        id="QUESTION1",
        surveyid="SURVEY1",
        questiontypecode="TYPECODE1",
        response="RESPONSE1",
    )
    question_2 = Question(
        id="QUESTION2",
        surveyid="SURVEY1",
        questiontypecode="TYPECODE2",
        response="RESPONSE2",
    )
    score = Score(
        id="SCORE1",
        surveyid="SURVEY1",
        scorevalue="SCORE_VALUE",
        scoretypecode="TYPECODE",
    )
    level = Level(
        id="LEVEL1",
        surveyid="SURVEY1",
        levelvalue="LEVEL_VALUE",
        leveltypecode="TYPECODE",
    )
    session.add(survey_1)

    session.add(question_1)
    session.add(question_2)
    session.add(score)
    session.add(level)

    document_pdf = Document(
        id="DOCUMENT_PDF",
        documentname="DOCUMENT_PDF_NAME",
        filename="DOCUMENT_PDF_FILENAME.pdf",
        pid=PID_1,
        documenttime=days_ago(365),
        repositoryupdatedate=datetime(2020, 3, 16),
    )
    document_pdf.stream = MINIMAL_PDF_BYTES
    document_pdf.filetype = "application/pdf"
    document_txt = Document(
        id="DOCUMENT_TXT",
        documentname="DOCUMENT_TXT_NAME",
        pid=PID_1,
        documenttime=days_ago(365),
        repositoryupdatedate=datetime(2020, 3, 16),
        notetext="DOCUMENT_TXT_NOTETEXT",
    )
    session.add(document_pdf)
    session.add(document_txt)

    modality_code_1 = ModalityCodes(
        registry_code="1",
        registry_code_desc="Haemodialysis - Acute",
        registry_code_type="HD",
        acute="0",  # BIT(1) field
        transfer_in="0",  # or use False
        ckd="0",
        cons="0",
        rrt="0",  # optional field
        end_of_care="0",
        is_imprecise="0",
        transfer_out="0",  # nullable=True in your model, so None is allowed too
    )
    session.add(modality_code_1)

    satellite_map_1 = SatelliteMap(satellite_code="TSF01", main_unit_code="TSF01")
    session.add(satellite_map_1)
    session.commit()


def populate_patient_2_extra(session):
    medication_3 = Medication(
        id="MEDICATION3",
        pid=PID_2,
        frequency="FREQUENCY_3",
        fromtime=days_ago(730),
        totime=days_ago(-999),
        drugproductgeneric="DRUG_PRODUCT_GENERIC_3",
        dosequantity=3,
        doseuomcode="DOSE_UOM_CODE_3",
        doseuomdesc="DOSE_UOM_DESCRIPTION_3",
        doseuomcodestd="DOSE_UOM_CODE_STD_3",
        repositoryupdatedate=datetime(2020, 3, 16),
    )

    session.add(medication_3)

    treatment_3 = Treatment(
        id="TREATMENT3",
        pid=PID_2,
        fromtime=days_ago(730),
        totime=days_ago(-999),
        admitreasoncode="1",
        admissionsourcecodestd="CF_RR7_TREATMENT",
        healthcarefacilitycode="TSF02",
        healthcarefacilitycodestd="ODS",
    )

    session.add(treatment_3)

    observation_2 = Observation(
        id="OBSERVATION2",
        pid=PID_2,
        observationcodestd="OBSERVATION_CODE_STD",
        observationcode="OBSERVATION_CODE",
        observationdesc="OBSERVATION_DESC",
        observationvalue="OBSERVATION_VALUE",
        observationunits="OBSERVATION_UNITS",
        observationtime=days_ago(365),
    )

    session.add(observation_2)

    survey_2 = Survey(
        id="SURVEY2",
        pid=PID_2,
        surveytime=days_ago(365),
        surveytypecode="TYPECODE",
        enteredbycode="ENTEREDBYCODE",
        enteredatcode="ENTEREDATCODE",
    )

    session.add(survey_2)

    session.commit()


def populate_workitems(session: Session):
    work_item_1 = WorkItem(
        id=1,
        personid=1,
        masterid=104,
        type=9,
        description="DESCRIPTION_1",
        status=1,
        creationdate=days_ago(365),
        lastupdated=days_ago(365),
    )

    work_item_2 = WorkItem(
        id=2,
        personid=2,
        masterid=104,
        type=9,
        description="DESCRIPTION_2",
        status=1,
        creationdate=days_ago(1),
        lastupdated=days_ago(1),
    )

    work_item_3 = WorkItem(
        id=3,
        personid=4,
        masterid=102,
        type=9,
        description="DESCRIPTION_3",
        status=1,
        creationdate=days_ago(1),
        lastupdated=days_ago(1),
    )

    work_item_closed = WorkItem(
        id=4,
        personid=4,
        masterid=101,
        type=9,
        description="DESCRIPTION_CLOSED",
        status=3,
        creationdate=days_ago(1),
        lastupdated=days_ago(1),
    )

    session.add(work_item_1)
    session.add(work_item_2)
    session.add(work_item_3)
    session.add(work_item_closed)

    session.commit()


def populate_all(ukrdc3: Session, jtrace: Session, errorsdb: Session, statsdb: Session):
    populate_facilities_and_messages(ukrdc3, statsdb, errorsdb)
    populate_codes(ukrdc3)

    # Create patients
    create_basic_patient(
        1,
        PID_1,
        UKRDCID_1,
        NI_1,
        "TSF01",
        "UKRDC",
        "00000000A",
        "Star",
        "Patrick",
        datetime(1984, 3, 17),
        ukrdc3,
        jtrace,
        datetime.now(),
    )
    create_basic_patient(
        2,
        PID_2,
        UKRDCID_2,
        NI_2,
        "TSF02",
        "UKRDC",
        "00000000B",
        "Tentacles",
        "Squidward",
        datetime(1975, 10, 9),
        ukrdc3,
        jtrace,
        datetime.now(),
    )
    create_basic_patient(
        3,
        PID_3,
        UKRDCID_3,
        NI_3,
        "TSF03",
        "UKRDC",
        "00000000A",
        "FAMILYNAME3",
        "GIVENNAME3",
        datetime(1984, 3, 17),
        ukrdc3,
        jtrace,
        datetime.now(),
    )
    create_basic_patient(
        4,
        PID_4,
        UKRDCID_4,
        NI_4,
        "TSF01",
        "UKRDC",
        "00000000B",
        "FAMILYNAME4",
        "GIVENNAME4",
        datetime(1975, 10, 9),
        ukrdc3,
        jtrace,
        datetime.now(),
    )
    # Link patients 1 and 4
    link_record = LinkRecord(
        id=401,
        personid=4,
        masterid=1,
        linktype=0,
        linkcode=0,
        lastupdated=days_ago(365),
    )
    jtrace.add(link_record)
    jtrace.commit()

    populate_patient_1_extra(ukrdc3)
    populate_patient_2_extra(ukrdc3)

    populate_workitems(jtrace)

    populate_basic_stats(statsdb)


@pytest.fixture(scope="function")
def jtrace_sessionmaker(postgresql_my):
    """
    Create a new function-scoped in-memory JTRACE database and return the session class
    """

    def dbcreator():
        return postgresql_my.cursor().connection

    engine = create_engine("postgresql+psycopg2://", creator=dbcreator)
    JtraceTestSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    JtraceBase.metadata.create_all(bind=engine)
    return JtraceTestSession


@pytest.fixture(scope="function")
def ukrdc3_sessionmaker(postgresql_my):
    """
    Create a new function-scoped in-memory UKRDC3 database and return the session class
    """

    def dbcreator():
        return postgresql_my.cursor().connection

    engine = create_engine("postgresql+psycopg2://", creator=dbcreator)
    ukrdc_test_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    UKRDC3Base.metadata.create_all(bind=engine)
    return ukrdc_test_session


@pytest.fixture(scope="function")
def errorsdb_sessionmaker(postgresql_my):
    """
    Create a new function-scoped in-memory ERRORS database and return the session class
    """

    def dbcreator():
        return postgresql_my.cursor().connection

    engine = create_engine("postgresql+psycopg2://", creator=dbcreator)
    errors_test_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    ErrorsBase.metadata.create_all(bind=engine)
    return errors_test_session


@pytest.fixture(scope="function")
def statsdb_sessionmaker(postgresql_my):
    """
    Create a new function-scoped in-memory STATS database and return the session class
    """

    def dbcreator():
        return postgresql_my.cursor().connection

    engine = create_engine("postgresql+psycopg2://", creator=dbcreator)
    stats_test_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    StatsBase.metadata.create_all(bind=engine)
    return stats_test_session


@pytest.fixture(scope="function")
def auditdb_sessionmaker(postgresql_my):
    """
    Create a new function-scoped in-memory AUDIT database and return the session class
    """

    def dbcreator():
        return postgresql_my.cursor().connection

    engine = create_engine("postgresql+psycopg2://", creator=dbcreator)
    stats_test_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    AuditBase.metadata.create_all(bind=engine)
    return stats_test_session


@pytest.fixture(scope="function")
def usersdb_sessionmaker():
    """
    Create a new function-scoped in-memory USERS database and return the session class
    """

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    users_test_session = sessionmaker(bind=engine)
    UsersBase.metadata.create_all(bind=engine)
    return users_test_session


@pytest.fixture(scope="function")
def sessions(
    ukrdc3_sessionmaker,
    jtrace_sessionmaker,
    errorsdb_sessionmaker,
    statsdb_sessionmaker,
    auditdb_sessionmaker,
    usersdb_sessionmaker,
):
    """
    Create a new function-scoped in-memory UKRDC3, JTRACE, ERRORS and STATS databases,
    populate with test data, and return the session classes
    """

    ukrdc3 = ukrdc3_sessionmaker()
    jtrace = jtrace_sessionmaker()
    errorsdb = errorsdb_sessionmaker()
    statsdb = statsdb_sessionmaker()
    auditdb = auditdb_sessionmaker()
    usersdb = usersdb_sessionmaker()

    populate_all(ukrdc3, jtrace, errorsdb, statsdb)

    yield ukrdc3, jtrace, errorsdb, statsdb, auditdb, usersdb

    ukrdc3.close()
    jtrace.close()
    errorsdb.close()
    statsdb.close()
    auditdb.close()
    usersdb.close()


@pytest.fixture(scope="function")
def ukrdc3_session(sessions):
    return sessions[0]


@pytest.fixture(scope="function")
def jtrace_session(sessions):
    return sessions[1]


@pytest.fixture(scope="function")
def errorsdb_session(sessions):
    return sessions[2]


@pytest.fixture(scope="function")
def stats_session(sessions):
    return sessions[3]


@pytest.fixture(scope="function")
def audit_session(sessions):
    return sessions[4]


@pytest.fixture(scope="function")
def users_session(sessions):
    return sessions[5]


@pytest_asyncio.fixture(scope="function")
async def mirth_session():
    """Create a fresh in-memory Mirth session"""
    async with MirthAPI("mock://mirth.url") as api:
        yield api


@pytest_asyncio.fixture(scope="function")
async def redis_session(httpx_session):
    """Create a fresh in-memory Redis database session"""
    redis = fakeredis.FakeStrictRedis(decode_responses=True, db=0)
    return redis


@pytest.fixture(scope="function")
def task_redis_sessions():
    """Create fresh in-memory Redis database sessions for task tracking"""
    return (
        fakeredis.FakeStrictRedis(decode_responses=True, db=1),
        fakeredis.FakeStrictRedis(decode_responses=True, db=2),
    )


@pytest.fixture(scope="function")
def app(
    jtrace_session,
    ukrdc3_session,
    errorsdb_session,
    stats_session,
    audit_session,
    users_session,
    redis_session,
    task_redis_sessions,
):
    from ukrdc_fastapi.main import app

    async def _get_mirth():
        async with MirthAPI("mock://mirth.url") as api:
            yield api

    def _get_redis():
        return redis_session

    def _get_ukrdc3():
        return ukrdc3_session

    def _get_jtrace():
        return jtrace_session

    def _get_errorsdb():
        return errorsdb_session

    def _get_statsdb():
        return stats_session

    def _get_auditdb():
        return audit_session

    def _get_usersdb():
        return users_session

    def _get_task_tracker(
        user: auth.UKRDCUser = Security(auth.auth.get_user()),
    ):
        return TaskTracker(task_redis_sessions[0], task_redis_sessions[1], user=user)

    def _get_root_task_tracker():
        return TaskTracker(
            task_redis_sessions[0], task_redis_sessions[1], user=auth.auth.superuser
        )

    # Override FastAPI dependencies to point to function-scoped sessions
    app.dependency_overrides[get_mirth] = _get_mirth
    app.dependency_overrides[get_redis] = _get_redis
    app.dependency_overrides[get_ukrdc3] = _get_ukrdc3
    app.dependency_overrides[get_jtrace] = _get_jtrace
    app.dependency_overrides[get_errorsdb] = _get_errorsdb
    app.dependency_overrides[get_statsdb] = _get_statsdb
    app.dependency_overrides[get_auditdb] = _get_auditdb
    app.dependency_overrides[get_usersdb] = _get_usersdb
    app.dependency_overrides[get_task_tracker] = _get_task_tracker
    app.dependency_overrides[get_root_task_tracker] = _get_root_task_tracker

    return app


@pytest_asyncio.fixture(scope="function")
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def app_authenticated(app):
    def _get_token():
        return {
            "uid": "TEST_ID",
            "cid": "PYTEST",
            "sub": "TEST@UKRDC_FASTAPI",
            "scp": ["openid", "profile", "email", "offline_access"],
            "org.ukrdc.permissions": [
                *Permissions.all()[:-1],
                "ukrdc:unit:TSF01",
            ],
        }

    app.dependency_overrides[auth.auth.okta_jwt_scheme] = _get_token

    return app


@pytest_asyncio.fixture(scope="function")
async def client_authenticated(app_authenticated):
    async with AsyncClient(app=app_authenticated, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def app_superuser(app):
    def _get_token():
        return {
            "uid": "TEST_ID",
            "cid": "PYTEST",
            "sub": "TEST@UKRDC_FASTAPI",
            "scp": ["openid", "profile", "email", "offline_access"],
            "org.ukrdc.permissions": auth.Permissions.all(),
        }

    app.dependency_overrides[auth.auth.okta_jwt_scheme] = _get_token

    return app


@pytest_asyncio.fixture(scope="function")
async def client_superuser(app_superuser):
    async with AsyncClient(app=app_superuser, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def non_mocked_hosts() -> list:
    return ["test"]


@pytest.fixture(scope="function")
def httpx_session(httpx_mock: HTTPXMock):
    # Override reset since we don't care if not all mocked routes are called
    def reset_override(*args):
        pass

    httpx_mock.reset = reset_override  #  type:ignore

    # Load a minimal channel response to mock a Mirth server
    responses_path = Path(__file__).resolve().parent.joinpath("responses")
    with open(responses_path.joinpath("channels.xml"), "r") as f:
        channels_response: str = f.read()
    with open(responses_path.joinpath("channelStatistics.xml"), "r") as f:
        channel_statistics_response: str = f.read()
    with open(responses_path.joinpath("channelGroups.xml"), "r") as f:
        channel_groups_response: str = f.read()
    with open(responses_path.joinpath("messageResponse.xml"), "r") as f:
        message_999_response: str = f.read()

    httpx_mock.add_response(
        method="GET",
        text=message_999_response,
        url=re.compile(r"mock:\/\/mirth.url\/channels\/.*\/messages\/.*"),
    )

    httpx_mock.add_response(
        method="POST",
        text="<long>999</long>",
        url=re.compile(r"mock:\/\/mirth.url\/channels\/.*\/messages"),
    )

    httpx_mock.add_response(
        url=re.compile(r"mock:\/\/mirth.url\/channels\/statistics"),
        text=channel_statistics_response,
    )

    httpx_mock.add_response(
        url=re.compile(r"mock:\/\/mirth.url\/channels"), text=channels_response
    )

    httpx_mock.add_response(
        url=re.compile(r"mock:\/\/mirth.url\/channelgroups"),
        text=channel_groups_response,
    )

    httpx_mock.add_response(
        status_code=204, url=re.compile(r"mock:\/\/mirth.url\/channels\/.*\/messages")
    )


@pytest.fixture(scope="function")
def superuser():
    return UKRDCUser(
        id="TEST_ID",
        cid="PYTEST",
        email="TEST@UKRDC_FASTAPI",
        permissions=Permissions.all(),
        scopes=["openid", "profile", "email", "offline_access"],
    )


@pytest.fixture(scope="function")
def user():
    return UKRDCUser(
        id="TEST_ID",
        cid="PYTEST",
        email="TEST@UKRDC_FASTAPI",
        permissions=[*Permissions.all()[:-1], "ukrdc:unit:TSF01"],
        scopes=["openid", "profile", "email", "offline_access"],
    )


@pytest.fixture()
def minimal_pdf():
    return MINIMAL_PDF_BYTES
