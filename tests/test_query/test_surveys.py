from ukrdc_fastapi.query import surveys


def test_get_surveys_superuser(ukrdc3_session, superuser):
    all_surveys = surveys.get_surveys(ukrdc3_session, superuser)
    assert {item.id for item in all_surveys} == {"SURVEY1", "SURVEY2"}


def test_get_surveys_denied(ukrdc3_session, test_user):
    all_surveys = surveys.get_surveys(ukrdc3_session, test_user)
    assert {item.id for item in all_surveys} == {"SURVEY1"}


def test_get_surveys_pid(ukrdc3_session, superuser):
    all_surveys = surveys.get_surveys(
        ukrdc3_session, superuser, pid="PYTEST01:PV:00000000A"
    )
    assert {item.id for item in all_surveys} == {"SURVEY1"}

    all_surveys = surveys.get_surveys(ukrdc3_session, superuser, pid="MADE_UP_PID")
    assert len(all_surveys.all()) == 0
