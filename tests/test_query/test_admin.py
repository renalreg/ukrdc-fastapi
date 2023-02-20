from ukrdc_fastapi.query import admin


def test_get_admin_counts(ukrdc3_session, jtrace_session, errorsdb_session):
    counts = admin.get_admin_counts(ukrdc3_session, jtrace_session, errorsdb_session)
    assert counts.open_workitems == 3
    assert counts.distinct_patients == 4
    assert counts.patients_receiving_errors == 2
