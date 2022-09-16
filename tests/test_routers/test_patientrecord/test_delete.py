from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef, WorkItem
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.delete import DeletePIDResponseSchema


async def test_delete_summary(client, ukrdc3_session, jtrace_session):
    response = await client.post(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/delete"
    )
    assert response.status_code == 200

    summary = DeletePIDResponseSchema(**response.json())

    # Assert all expected records exist
    assert ukrdc3_session.query(PatientRecord).get("PYTEST03:PV:00000000A")
    for person in summary.empi.persons:
        assert jtrace_session.query(Person).get(person.id)
    for master_record in summary.empi.master_records:
        assert jtrace_session.query(MasterRecord).get(master_record.id)
    for pidxref in summary.empi.pidxrefs:
        assert jtrace_session.query(PidXRef).get(pidxref.id)
    for work_item in summary.empi.work_items:
        assert jtrace_session.query(WorkItem).get(work_item.id)
    for link_record in summary.empi.link_records:
        assert jtrace_session.query(LinkRecord).get(link_record.id)


async def test_delete(client, ukrdc3_session, jtrace_session):
    response = await client.post(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/delete"
    )
    assert response.status_code == 200

    summary = DeletePIDResponseSchema(**response.json())

    # Assert all expected records exist
    assert ukrdc3_session.query(PatientRecord).get("PYTEST03:PV:00000000A")
    for person in summary.empi.persons:
        assert jtrace_session.query(Person).get(person.id)
    for master_record in summary.empi.master_records:
        assert jtrace_session.query(MasterRecord).get(master_record.id)
    for pidxref in summary.empi.pidxrefs:
        assert jtrace_session.query(PidXRef).get(pidxref.id)
    for work_item in summary.empi.work_items:
        assert jtrace_session.query(WorkItem).get(work_item.id)
    for link_record in summary.empi.link_records:
        assert jtrace_session.query(LinkRecord).get(link_record.id)

    deleted_response = await client.post(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/delete",
        json={"hash": summary.hash},
    )
    assert deleted_response.status_code == 200

    deleted = DeletePIDResponseSchema(**deleted_response.json())

    assert deleted.committed == True
    assert deleted.hash == summary.hash

    # Assert all expected records have been deleted
    assert not ukrdc3_session.query(PatientRecord).get("PYTEST03:PV:00000000A")
    for person in summary.empi.persons:
        assert not jtrace_session.query(Person).get(person.id)
    for master_record in summary.empi.master_records:
        assert not jtrace_session.query(MasterRecord).get(master_record.id)
    for pidxref in summary.empi.pidxrefs:
        assert not jtrace_session.query(PidXRef).get(pidxref.id)
    for work_item in summary.empi.work_items:
        assert not jtrace_session.query(WorkItem).get(work_item.id)
    for link_record in summary.empi.link_records:
        assert not jtrace_session.query(LinkRecord).get(link_record.id)


async def test_delete_badhash(client, ukrdc3_session):
    response = await client.post(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/delete",
        json={"hash": "BADHASH"},
    )
    assert response.status_code == 400

    # Assert expected record still exists
    assert ukrdc3_session.query(PatientRecord).get("PYTEST03:PV:00000000A")
