import pytest

from ukrdc_fastapi.query.common import PermissionsError
from ukrdc_fastapi.query.facilities import stats

from ..utils import days_ago

# NOTE: We assume that core functionality has been tested within the ukrdc_stats library,
#       so we only need to test integration with the API here (permissions etc).
#       I'm also assuming that the responsibility of maintaining API compatibility lies
#       with the stats library. We have tests in that library which expect a specific output
#       schema, so this should be reasonable. Additionally, any changes should get picked up
#       by type checks in the client libraries as a final layer of safety.


def test_get_facility_demographic_stats(ukrdc3_session, superuser):
    demogs = stats.get_facility_demographic_stats(
        ukrdc3_session, "TEST_SENDING_FACILITY_1", superuser
    )
    # Basic check that the cohort is valid
    assert demogs.metadata.population == 2


def test_get_facility_demographic_stats_denied(ukrdc3_session, test_user):
    with pytest.raises(PermissionsError):
        stats.get_facility_demographic_stats(
            ukrdc3_session, "TEST_SENDING_FACILITY_2", test_user
        )


def test_get_facility_dialysis_stats(ukrdc3_session, superuser):
    dias = stats.get_facility_dialysis_stats(
        ukrdc3_session, "TEST_SENDING_FACILITY_1", superuser
    )
    # Basic check that the cohort is valid
    # Only PID_1 has treatment records added for testing
    assert dias.metadata.population == 1
    # Ensure we're defaulting to 90 day extract
    assert dias.metadata.from_time.date() == days_ago(90).date()


def test_get_facility_dialysis_stats_denied(ukrdc3_session, test_user):
    with pytest.raises(PermissionsError):
        stats.get_facility_dialysis_stats(
            ukrdc3_session, "TEST_SENDING_FACILITY_2", test_user
        )
