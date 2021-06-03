from ukrdc_fastapi.query import medications


def test_get_medications_superuser(ukrdc3_session, superuser):
    all_meds = medications.get_medications(ukrdc3_session, superuser)
    assert {record.id for record in all_meds} == {
        "MEDICATION1",
        "MEDICATION2",
        "MEDICATION3",
    }


def test_get_medications_denied(ukrdc3_session, test_user):
    all_meds = medications.get_medications(ukrdc3_session, test_user)
    assert {record.id for record in all_meds} == {
        "MEDICATION1",
        "MEDICATION2",
    }


def test_get_medications_pid(ukrdc3_session, superuser):
    all_meds = medications.get_medications(
        ukrdc3_session, superuser, pid="PYTEST01:PV:00000000A"
    )
    assert {record.id for record in all_meds} == {"MEDICATION1", "MEDICATION2"}

    all_meds = medications.get_medications(ukrdc3_session, superuser, pid="MADE_UP_PID")
    assert len(all_meds.all()) == 0
