import re
from datetime import datetime
from pathlib import Path

import fakeredis
import pytest
from fastapi.testclient import TestClient
from mirth_client import MirthAPI
from pytest_httpx import HTTPXMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from ukrdc_sqla.empi import Base as JtraceBase
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef, WorkItem
from ukrdc_sqla.errorsdb import Base as ErrorsBase
from ukrdc_sqla.errorsdb import Message as ErrorMessage
from ukrdc_sqla.pkb import PKBLink
from ukrdc_sqla.ukrdc import Address
from ukrdc_sqla.ukrdc import Base as UKRDC3Base
from ukrdc_sqla.ukrdc import (
    Code,
    Diagnosis,
    Document,
    LabOrder,
    Level,
    Medication,
    Name,
    Observation,
    Patient,
    PatientNumber,
    PatientRecord,
    Question,
    RenalDiagnosis,
    ResultItem,
    Score,
    Survey,
)

from ukrdc_fastapi.dependencies import (
    auth,
    get_errorsdb,
    get_jtrace,
    get_mirth,
    get_redis,
    get_ukrdc3,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser

# FastAPI dependency override gets confused by some of our auth stuff,
# so we'll do a dirty patch for testing


class FakeAuth(auth.URKDCAuth):
    def __init__(self, *_) -> None:
        pass

    def oidc_scheme(self):
        return

    def get_user(self):
        return UKRDCUser(
            id="TEST_ID",
            email="TEST@UKRDC_FASTAPI",
            permissions=self.permissions.all(),
            scopes=["openid", "profile", "email", "offline_access"],
        )

    def scope(self, *_):
        def scope_dependency():
            return

        return scope_dependency

    def permission(self, *_):
        def permission_dependency():
            return

        return permission_dependency


auth.auth = FakeAuth()


def populate_ukrdc3_session(session):

    code1 = Code(
        coding_standard="RR1+",
        code="TEST_SENDING_FACILITY_1",
        description="TEST_SENDING_FACILITY_1_DESCRIPTION",
    )
    code2 = Code(
        coding_standard="RR1+",
        code="TEST_SENDING_FACILITY_2",
        description="TEST_SENDING_FACILITY_2_DESCRIPTION",
    )
    session.add(code1)
    session.add(code2)

    pid_1: str = "PYTEST01:PV:00000000A"
    pid_2: str = "PYTEST02:PV:00000000A"

    patient_record_1 = PatientRecord(
        pid=pid_1,
        sendingfacility="TEST_SENDING_FACILITY_1",
        sendingextract="PV",
        localpatientid="00000000A",
        ukrdcid="000000000",
        repository_update_date=datetime(2020, 3, 16),
        repository_creation_date=datetime(2020, 3, 16),
    )
    patient_record_1.update_date = datetime(2021, 1, 21)
    patient_record_1.repository_update_date = datetime(2021, 1, 21)
    session.add(patient_record_1)

    patient_record_2 = PatientRecord(
        pid=pid_2,
        sendingfacility="TEST_SENDING_FACILITY_2",
        sendingextract="PV",
        localpatientid="00000000B",
        ukrdcid="000000001",
        repository_update_date=datetime(2020, 3, 16),
        repository_creation_date=datetime(2020, 3, 16),
    )
    patient_record_2.update_date = datetime(2021, 1, 21)
    patient_record_2.repository_update_date = datetime(2021, 1, 21)
    session.add(patient_record_2)

    name = Name(id=1, pid=pid_1, family="Star", given="Patrick", nameuse="L")
    address = Address(
        id="ADDRESS1",
        pid=pid_1,
        street="120 Conch Street",
        town="Bikini Bottom",
        county="Bikini County",
        postcode="XX0 1AA",
        country_description="Pacific Ocean",
    )
    address_alt = Address(
        id="ADDRESS2",
        pid=pid_1,
        street="121 Conch Street",
        town="Bikini Bottom",
        county="Bikini County",
        postcode="XX0 1AA",
        country_description="Pacific Ocean",
    )
    patient = Patient(pid=pid_1, birth_time=datetime(1984, 3, 17), gender="1")
    patient_number = PatientNumber(
        id=1, pid=pid_1, patientid="999999999", organization="NHS", numbertype="NI"
    )
    session.add(name)
    session.add(address)
    session.add(address_alt)
    session.add(patient)
    session.add(patient_number)

    diagnosis_1 = Diagnosis(
        id="DIAGNOSIS1",
        pid=pid_1,
        diagnosis_code="DIAGNOSIS_CODE",
        diagnosis_code_std="DIAGNOSIS_CODE_STD",
        diagnosis_desc="DIAGNOSIS_DESCRIPTION",
        identification_time=datetime(2020, 3, 16),
        onset_time=datetime(2019, 3, 16),
        comments="DIAGNOSIS_COMMENTS",
    )
    pkb_link_1 = PKBLink(
        coding_standard="DIAGNOSIS",
        code="DIAGNOSIS_CODE",
        link="http://pkb_link.1",
        link_name="PKB_LINK_1",
    )
    diagnosis_2 = Diagnosis(
        id="DIAGNOSIS2",
        pid=pid_1,
        diagnosis_code="DIAGNOSIS_CODE_2",
        diagnosis_code_std="DIAGNOSIS_CODE_STD_2",
        identification_time=datetime(2020, 3, 16),
        onset_time=datetime(2019, 3, 16),
        comments="DIAGNOSIS_COMMENTS_2",
    )
    pkb_link_2 = PKBLink(
        coding_standard="DIAGNOSIS",
        code="DIAGNOSIS_CODE_2",
        link="http://pkb_link.2",
        link_name="PKB_LINK_2",
    )
    session.add(diagnosis_1)
    session.add(pkb_link_1)
    session.add(diagnosis_2)
    session.add(pkb_link_2)

    renal_diagnosis_1 = RenalDiagnosis(
        pid=pid_1,
        diagnosis_code="R_DIAGNOSIS_CODE",
        diagnosis_code_std="R_DIAGNOSIS_CODE_STD",
        diagnosis_desc="R_DIAGNOSIS_DESCRIPTION",
        identification_time=datetime(2020, 3, 16),
        comments="R_DIAGNOSIS_COMMENTS",
    )
    renal_pkb_link_2 = PKBLink(
        coding_standard="TREATMENT",
        code="R_DIAGNOSIS_CODE",
        link="http://renal_pkb_link.2",
        link_name="RENAL_PKB_LINK_2",
    )
    session.add(renal_diagnosis_1)
    session.add(renal_pkb_link_2)

    medication_1 = Medication(
        id="MEDICATION1",
        pid=pid_1,
        frequency="FREQUENCY",
        from_time=datetime(2019, 3, 16),
        to_time=None,
        drug_product_generic="DRUG_PRODUCT_GENERIC",
        dose_quantity="DOSE_QUANTITY",
        dose_uom_code="DOSE_UOM_CODE",
        dose_uom_description="DOSE_UOM_DESCRIPTION",
        dose_uom_code_std="DOSE_UOM_CODE_STD",
    )
    medication_2 = Medication(
        id="MEDICATION2",
        pid=pid_1,
        frequency="FREQUENCY_2",
        from_time=datetime(2019, 3, 16),
        to_time=datetime(9999, 3, 16),
        drug_product_generic="DRUG_PRODUCT_GENERIC_2",
        dose_quantity="DOSE_QUANTITY_2",
        dose_uom_code="DOSE_UOM_CODE_2",
        dose_uom_description="DOSE_UOM_DESCRIPTION_2",
        dose_uom_code_std="DOSE_UOM_CODE_STD_2",
    )
    medication_3 = Medication(
        id="MEDICATION3",
        pid=pid_2,
        frequency="FREQUENCY_3",
        from_time=datetime(2019, 3, 16),
        to_time=datetime(9999, 3, 16),
        drug_product_generic="DRUG_PRODUCT_GENERIC_3",
        dose_quantity="DOSE_QUANTITY_3",
        dose_uom_code="DOSE_UOM_CODE_3",
        dose_uom_description="DOSE_UOM_DESCRIPTION_3",
        dose_uom_code_std="DOSE_UOM_CODE_STD_3",
    )
    session.add(medication_1)
    session.add(medication_2)
    session.add(medication_3)

    laborder_1 = LabOrder(
        id="LABORDER1",
        entered_at="TEST_SENDING_FACILITY_1",
        pid=pid_1,
        external_id="EXTERNAL_ID_1",
        order_category="ORDER_CATEGORY",
        specimen_collected_time=datetime(2020, 3, 16),
    )
    resultitem_1 = ResultItem(
        id="RESULTITEM1",
        order_id="LABORDER1",
        service_id_std="SERVICE_ID_STD",
        service_id="SERVICE_ID_1",
        service_id_description="SERVICE_ID_DESCRIPTION",
        value="VALUE",
        value_units="VALUE_UNITS",
        observation_time=datetime(2020, 3, 16),
    )
    laborder_2 = LabOrder(
        id="LABORDER2",
        entered_at="TEST_SENDING_FACILITY_2",
        pid=pid_1,
        external_id="EXTERNAL_ID_2",
        order_category="ORDER_CATEGORY",
        specimen_collected_time=datetime(2021, 1, 1),
    )
    resultitem_2 = ResultItem(
        id="RESULTITEM2",
        order_id="LABORDER2",
        service_id_std="SERVICE_ID_STD",
        service_id="SERVICE_ID_2",
        service_id_description="SERVICE_ID_DESCRIPTION",
        value="VALUE",
        value_units="VALUE_UNITS",
        observation_time=datetime(2021, 1, 1),
    )
    session.add(laborder_1)
    session.add(resultitem_1)
    session.add(laborder_2)
    session.add(resultitem_2)

    observation_1 = Observation(
        id="OBSERVATION1",
        pid=pid_1,
        observation_code_std="OBSERVATION_CODE_STD",
        observation_code="OBSERVATION_CODE",
        observation_desc="OBSERVATION_DESC",
        observation_value="OBSERVATION_VALUE",
        observation_units="OBSERVATION_UNITS",
        observation_time=datetime(2020, 3, 16),
    )
    observation_2 = Observation(
        id="OBSERVATION2",
        pid=pid_2,
        observation_code_std="OBSERVATION_CODE_STD",
        observation_code="OBSERVATION_CODE",
        observation_desc="OBSERVATION_DESC",
        observation_value="OBSERVATION_VALUE",
        observation_units="OBSERVATION_UNITS",
        observation_time=datetime(2020, 3, 16),
    )
    session.add(observation_1)
    session.add(observation_2)

    observation_dia = Observation(
        id="OBSERVATION_DIA_1",
        pid=pid_1,
        observation_code_std="PV",
        observation_code="bpdia",
        observation_desc="OBSERVATION_DIA_1_DESC",
        observation_value="OBSERVATION_DIA_1_VALUE",
        observation_units="OBSERVATION_DIA_1_UNITS",
        observation_time=datetime(2020, 3, 16, 11, 30, 00),
    )
    observation_sys = Observation(
        id="OBSERVATION_SYS_1",
        pid=pid_1,
        observation_code_std="PV",
        observation_code="bpsys",
        observation_desc="OBSERVATION_SYS_1_DESC",
        observation_value="OBSERVATION_SYS_1_VALUE",
        observation_units="OBSERVATION_SYS_1_UNITS",
        observation_time=datetime(2020, 3, 16, 11, 35, 00),
    )
    session.add(observation_dia)
    session.add(observation_sys)

    survey_1 = Survey(
        id="SURVEY1",
        pid=pid_1,
        surveytime=datetime(2020, 3, 16, 18, 00),
        surveytypecode="TYPECODE",
        enteredbycode="ENTEREDBYCODE",
        enteredatcode="ENTEREDATCODE",
    )
    survey_2 = Survey(
        id="SURVEY2",
        pid=pid_2,
        surveytime=datetime(2020, 3, 16, 18, 00),
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
        id="SCORE1", surveyid="SURVEY1", value="SCORE_VALUE", scoretypecode="TYPECODE"
    )
    level = Level(
        id="LEVEL1", surveyid="SURVEY1", value="LEVEL_VALUE", leveltypecode="TYPECODE"
    )
    session.add(survey_1)
    session.add(survey_2)
    session.add(question_1)
    session.add(question_2)
    session.add(score)
    session.add(level)

    document_pdf = Document(
        id="DOCUMENT_PDF", pid=pid_1, documenttime=datetime(2020, 3, 16)
    )
    document_pdf.stream = (
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
    document_pdf.filetype = "application/pdf"
    document_txt = Document(
        id="DOCUMENT_TXT",
        pid=pid_1,
        documenttime=datetime(2020, 3, 16),
        notetext="DOCUMENT_TXT_NOTETEXT",
    )
    session.add(document_pdf)
    session.add(document_txt)

    session.commit()


def populate_jtrace_session(session):
    master_record_1 = MasterRecord(
        id=1,
        status=0,
        last_updated=datetime(2020, 3, 16),
        date_of_birth=datetime(1950, 1, 1),
        nationalid="999999999",
        nationalid_type="UKRDC",
        effective_date=datetime(2020, 3, 16),
    )

    master_record_2 = MasterRecord(
        id=2,
        status=0,
        last_updated=datetime(2021, 1, 1),
        date_of_birth=datetime(1980, 12, 12),
        nationalid="999999911",
        nationalid_type="UKRDC",
        effective_date=datetime(2021, 1, 1),
    )

    person_1 = Person(
        id=1,
        originator="UKRDC",
        localid="PYTEST01:PV:00000000A",
        localid_type="CLPID",
        date_of_birth=datetime(1950, 1, 1),
        gender="9",
    )

    person_1_xref_1 = PidXRef(
        id=1,
        pid="PYTEST01:PV:00000000A",
        sending_facility="TEST_SENDING_FACILITY_1",
        sending_extract="XREF_SENDING_EXTRACT_1",
        localid="XREF_LOCALID_1",
    )

    person_2 = Person(
        id=2,
        originator="UKRDC",
        localid="PYTEST02:PV:00000000A",
        localid_type="CLPID",
        date_of_birth=datetime(1950, 1, 1),
        gender="9",
    )
    person_2_xref_1 = PidXRef(
        id=2,
        pid="PYTEST02:PV:00000000A",
        sending_facility="TEST_SENDING_FACILITY_2",
        sending_extract="XREF_SENDING_EXTRACT_2",
        localid="XREF_LOCALID_2",
    )

    person_3 = Person(
        id=3,
        originator="UKRDC",
        localid="PYTEST03:PV:00000000A",
        localid_type="CLPID",
        date_of_birth=datetime(1950, 1, 1),
        gender="9",
    )

    person_4 = Person(
        id=4,
        originator="UKRDC",
        localid="PYTEST04:PV:00000000A",
        localid_type="CLPID",
        date_of_birth=datetime(1950, 1, 1),
        gender="9",
    )
    person_4_xref_1 = PidXRef(
        id=3,
        pid="PYTEST04:PV:00000000A",
        sending_facility="TEST_SENDING_FACILITY_1",
        sending_extract="XREF_SENDING_EXTRACT_1",
        localid="XREF_LOCALID_1",
    )

    link_record_1 = LinkRecord(
        id=1,
        person_id=1,
        master_id=1,
        link_type=0,
        link_code=0,
        last_updated=datetime(2019, 1, 1),
    )
    link_record_2 = LinkRecord(
        id=2,
        person_id=2,
        master_id=1,
        link_type=0,
        link_code=0,
        last_updated=datetime(2020, 3, 16),
    )

    work_item_1 = WorkItem(
        id=1,
        person_id=3,
        master_id=1,
        type=9,
        description="DESCRIPTION_1",
        status=1,
        last_updated=datetime(2020, 3, 16),
    )

    work_item_2 = WorkItem(
        id=2,
        person_id=4,
        master_id=1,
        type=9,
        description="DESCRIPTION_2",
        status=1,
        last_updated=datetime(2021, 1, 1),
    )

    work_item_3 = WorkItem(
        id=3,
        person_id=4,
        master_id=2,
        type=9,
        description="DESCRIPTION_3",
        status=1,
        last_updated=datetime(2021, 1, 1),
    )

    work_item_closed = WorkItem(
        id=4,
        person_id=1,
        master_id=1,
        type=9,
        description="DESCRIPTION_CLOSED",
        status=3,
        last_updated=datetime(2021, 1, 1),
    )

    session.add(master_record_1)
    session.add(master_record_2)
    session.add(person_1)
    session.add(person_1_xref_1)
    session.add(person_2)
    session.add(person_2_xref_1)
    session.add(person_3)
    session.add(person_4)
    session.add(person_4_xref_1)
    session.add(link_record_1)
    session.add(link_record_2)
    session.add(work_item_1)
    session.add(work_item_2)
    session.add(work_item_3)
    session.add(work_item_closed)

    session.commit()


def populate_errorsdb_session(session):
    # Mock error relating to MR 1, WORKITEMS 1 and 2
    error_1 = ErrorMessage(
        id=1,
        message_id=1,
        channel_id="MIRTH-CHANNEL-UUID",
        received=datetime(2021, 1, 1),
        msg_status="ERROR",
        ni="999999999",
        filename="FILENAME_1.XML",
        facility="TEST_SENDING_FACILITY_1",
        error="ERROR MESSAGE 1",
        status="STATUS1",
    )

    # Mock error unrelated to workitems
    error_2 = ErrorMessage(
        id=2,
        message_id=2,
        channel_id="MIRTH-CHANNEL-UUID",
        received=datetime(2020, 3, 16),
        msg_status="ERROR",
        ni=None,
        filename="FILENAME_2.XML",
        facility="TEST_SENDING_FACILITY_2",
        error="ERROR MESSAGE 2",
        status="STATUS2",
    )

    session.add(error_1)
    session.add(error_2)

    session.commit()


@pytest.fixture(scope="function")
def jtrace_sessionmaker():
    """
    Create a new function-scoped in-memory JTRACE database,
    populate with test data, and return the session class
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    JtraceTestSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    JtraceBase.metadata.create_all(bind=engine)
    populate_jtrace_session(JtraceTestSession())
    return JtraceTestSession


@pytest.fixture(scope="function")
def ukrdc3_sessionmaker():
    """
    Create a new function-scoped in-memory UKRDC3 database,
    populate with test data, and return the session class
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    UKRDCTestSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    UKRDC3Base.metadata.create_all(bind=engine)
    populate_ukrdc3_session(UKRDCTestSession())
    return UKRDCTestSession


@pytest.fixture(scope="function")
def errorsdb_sessionmaker():
    """
    Create a new function-scoped in-memory ERRORS database,
    populate with test data, and return the session class
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    ErrorsTestSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    ErrorsBase.metadata.create_all(bind=engine)
    populate_errorsdb_session(ErrorsTestSession())
    return ErrorsTestSession


@pytest.fixture(scope="function")
def ukrdc3_session(ukrdc3_sessionmaker):
    """Create and yield a fresh in-memory test UKRDC3 database session"""
    db = ukrdc3_sessionmaker()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def jtrace_session(jtrace_sessionmaker):
    """Create and yield a fresh in-memory test JTRACE database session"""
    db = jtrace_sessionmaker()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def errorsdb_session(errorsdb_sessionmaker):
    """Create and yield a fresh in-memory test ERRORS database session"""
    db = errorsdb_sessionmaker()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def redis_session():
    """Create a fresh in-memory Redis database session"""
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture(scope="function")
async def mirth_session():
    """Create a fresh in-memory Mirth session"""
    async with MirthAPI("mock://mirth.url") as api:
        yield api


@pytest.fixture(scope="function")
def app(jtrace_session, ukrdc3_session, errorsdb_session, redis_session):
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

    # Override FastAPI dependencies to point to function-scoped sessions
    app.dependency_overrides[get_mirth] = _get_mirth
    app.dependency_overrides[get_redis] = _get_redis
    app.dependency_overrides[get_ukrdc3] = _get_ukrdc3
    app.dependency_overrides[get_jtrace] = _get_jtrace
    app.dependency_overrides[get_errorsdb] = _get_errorsdb

    return app


@pytest.fixture(scope="function")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="function")
def httpx_session(httpx_mock: HTTPXMock):

    # Override reset since we don't care if not all mocked routes are called
    def reset_override(*args):
        pass

    httpx_mock.reset = reset_override

    # Load a minimal channel response to mock a Mirth server
    responses_path = Path(__file__).resolve().parent.joinpath("responses")
    with open(responses_path.joinpath("channels.xml"), "r") as f:
        channels_response: str = f.read()
    with open(responses_path.joinpath("channelStatistics.xml"), "r") as f:
        channel_statistics_response: str = f.read()
    with open(responses_path.joinpath("channelGroups.xml"), "r") as f:
        channel_groups_response: str = f.read()

    httpx_mock.add_response(
        url=re.compile(r"mock:\/\/mirth.url\/channels"), data=channels_response
    )
    httpx_mock.add_response(
        url=re.compile(r"mock:\/\/mirth.url\/channels\/statistics"),
        data=channel_statistics_response,
    )
    httpx_mock.add_response(
        url=re.compile(r"mock:\/\/mirth.url\/channelgroups"),
        data=channel_groups_response,
    )

    httpx_mock.add_response(
        status_code=204, url=re.compile(r"mock:\/\/mirth.url\/channels\/.*\/messages")
    )


@pytest.fixture(scope="function")
def superuser():
    return UKRDCUser(
        id="TEST_ID",
        email="TEST@UKRDC_FASTAPI",
        permissions=Permissions.all(),
        scopes=["openid", "profile", "email", "offline_access"],
    )


@pytest.fixture(scope="function")
def test_user():
    return UKRDCUser(
        id="TEST_ID",
        email="TEST@UKRDC_FASTAPI",
        permissions=[*Permissions.all()[:-1], "ukrdc:unit:TEST_SENDING_FACILITY_1"],
        scopes=["openid", "profile", "email", "offline_access"],
    )
