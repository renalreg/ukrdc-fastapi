from ukrdc_fastapi.query import observations


def test_get_observations_superuser(ukrdc3_session, superuser):
    all_obs = observations.get_observations(ukrdc3_session, superuser)
    assert {record.id for record in all_obs} == {
        "OBSERVATION1",
        "OBSERVATION2",
        "OBSERVATION_DIA_1",
        "OBSERVATION_SYS_1",
    }


def test_get_observations_denied(ukrdc3_session, test_user):
    all_obs = observations.get_observations(ukrdc3_session, test_user)
    assert {record.id for record in all_obs} == {
        "OBSERVATION1",
        "OBSERVATION_DIA_1",
        "OBSERVATION_SYS_1",
    }


def test_get_observations_pid(ukrdc3_session, superuser):
    all_obs = observations.get_observations(
        ukrdc3_session, superuser, pid="PYTEST01:PV:00000000A"
    )
    assert {record.id for record in all_obs} == {
        "OBSERVATION1",
        "OBSERVATION_DIA_1",
        "OBSERVATION_SYS_1",
    }

    all_obs = observations.get_observations(
        ukrdc3_session, superuser, pid="MADE_UP_PID"
    )
    assert len(all_obs.all()) == 0


def test_get_observations_code(ukrdc3_session, superuser):
    all_obs = observations.get_observations(
        ukrdc3_session, superuser, codes=["OBSERVATION_CODE"]
    )
    assert {record.id for record in all_obs} == {"OBSERVATION1", "OBSERVATION2"}


def test_get_observation_codes(ukrdc3_session, superuser):
    all_codes = observations.get_observation_codes(ukrdc3_session, superuser)
    assert all_codes == {"OBSERVATION_CODE", "bpdia", "bpsys"}
