from ukrdc_sqla.ukrdc import (
    Diagnosis,
    RenalDiagnosis,
    Code,
    PatientRecord,
    CauseOfDeath,
)

from ukrdc_fastapi.query.patientrecords.diagnoses import (
    get_patient_cause_of_death,
    get_patient_diagnosis,
    get_patient_renal_diagnosis,
)

from ...utils import days_ago
from ...conftest import PID_1


def _add_extra_diagnoses(session):
    diagnosis_1 = Diagnosis(
        id="DIAGNOSIS1",
        pid=PID_1,
        diagnosiscode="DIAGNOSIS_CODE",
        diagnosiscodestd="DIAGNOSIS_CODE_STD",
        diagnosisdesc="DIAGNOSIS_DESCRIPTION",
        identificationtime=days_ago(365),
        onsettime=days_ago(730),
        comments="DIAGNOSIS_COMMENTS",
    )

    code_1 = Code(
        coding_standard="DIAGNOSIS_CODE_STD",
        code="DIAGNOSIS_CODE",
        description="DESCRIPTION_1",
        creation_date=days_ago(365),
    )

    diagnosis_2 = Diagnosis(
        id="DIAGNOSIS2",
        pid=PID_1,
        diagnosiscode="DIAGNOSIS_CODE_2",
        diagnosiscodestd="DIAGNOSIS_CODE_STD_2",
        identificationtime=days_ago(365),
        onsettime=days_ago(730),
        comments="DIAGNOSIS_COMMENTS_2",
    )
    code_2 = Code(
        coding_standard="DIAGNOSIS_CODE_STD_2",
        code="DIAGNOSIS_CODE_2",
        description="DESCRIPTION_2",
        creation_date=days_ago(365),
    )

    session.add(diagnosis_1)
    session.add(code_1)
    session.add(diagnosis_2)
    session.add(code_2)

    renal_diagnosis_1 = RenalDiagnosis(
        pid=PID_1,
        diagnosiscode="R_DIAGNOSIS_CODE",
        diagnosiscodestd="R_DIAGNOSIS_CODE_STD",
        diagnosisdesc="R_DIAGNOSIS_DESCRIPTION",
        identificationtime=days_ago(365),
        comments="R_DIAGNOSIS_COMMENTS",
    )
    code_3 = Code(
        coding_standard="R_DIAGNOSIS_CODE_STD",
        code="R_DIAGNOSIS_CODE",
        description="DESCRIPTION_3",
        creation_date=days_ago(365),
    )

    session.add(renal_diagnosis_1)
    session.add(code_3)

    cause_of_death_1 = CauseOfDeath(
        pid=PID_1,
        diagnosiscode="D_DIAGNOSIS_CODE",
        diagnosiscodestd="D_DIAGNOSIS_CODE_STD",
        diagnosisdesc="D_DIAGNOSIS_DESCRIPTION",
        comments="D_DIAGNOSIS_COMMENTS",
    )
    code_4 = Code(
        coding_standard="D_DIAGNOSIS_CODE_STD",
        code="D_DIAGNOSIS_CODE",
        description="DESCRIPTION_4",
        creation_date=days_ago(365),
    )

    session.add(cause_of_death_1)
    session.add(code_4)

    session.commit()


def test_get_patient_diagnosis(ukrdc3_session):
    _add_extra_diagnoses(ukrdc3_session)
    record = ukrdc3_session.get(PatientRecord, PID_1)

    diagnoses = get_patient_diagnosis(record, ukrdc3_session)

    # Check all rows are returned
    assert len(diagnoses) == 2
    # Check code lookup works
    assert diagnoses[0].description == "DESCRIPTION_1"
    assert diagnoses[1].description == "DESCRIPTION_2"


def test_get_patient_renal_diagnosis(ukrdc3_session):
    _add_extra_diagnoses(ukrdc3_session)
    record = ukrdc3_session.get(PatientRecord, PID_1)

    renal_diagnoses = get_patient_renal_diagnosis(record, ukrdc3_session)

    # Check all rows are returned
    assert len(renal_diagnoses) == 1
    # Check code lookup works
    assert renal_diagnoses[0].description == "DESCRIPTION_3"


def test_get_patient_cause_of_death(ukrdc3_session):
    _add_extra_diagnoses(ukrdc3_session)
    record = ukrdc3_session.get(PatientRecord, PID_1)

    cause_of_death = get_patient_cause_of_death(record, ukrdc3_session)

    # Check all rows are returned
    assert len(cause_of_death) == 1
    # Check code lookup works
    assert cause_of_death[0].description == "DESCRIPTION_4"
