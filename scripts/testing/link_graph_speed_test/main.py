from time import time
from typing import Any, List

from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.empi import LinkRecord, MasterRecord

from ukrdc_fastapi.dependencies.database import JtraceSession


class Timer(object):
    def __init__(self, description):
        self.description = description

    def __enter__(self):
        self.start = time()

    def __exit__(self, type, value, traceback):
        self.end = time()
        print(f"{self.description}: {self.end - self.start}")


def native(jtrace: Session, seen_master_ids: set[int], seen_person_ids: set[int]):
    found_new: bool = True
    while found_new:
        links: list[LinkRecord] = (
            jtrace.query(LinkRecord)
            .filter(
                (LinkRecord.master_id.in_(seen_master_ids))
                | (LinkRecord.person_id.in_(seen_person_ids))
            )
            .all()
        )

        master_ids: set[int] = {item.master_id for item in links}
        person_ids: set[int] = {item.person_id for item in links}
        if seen_master_ids.issuperset(master_ids) and seen_person_ids.issuperset(
            person_ids
        ):
            found_new = False
        seen_master_ids |= master_ids
        seen_person_ids |= person_ids
    return seen_master_ids, seen_person_ids


def sql(jtrace: Session, seen_master_ids: set[int], seen_person_ids: set[int]):
    """
    Construct sets of related master records and person records.
    This performs a recursive search of associated link records,
    fetching the master and person record IDs from each link record.
    """
    mr_set = set()
    pr_set = set()

    # Base CTE
    base = (
        select(LinkRecord.master_id, LinkRecord.person_id)
        .where(
            LinkRecord.master_id.in_(seen_master_ids)
            | LinkRecord.person_id.in_(seen_person_ids)
        )
    )
    cte = base.cte(name="cte", recursive=True)

    # Recursive part
    recursive = (
        select(LinkRecord.master_id, LinkRecord.person_id)
        .join(
            cte,
            or_(
                LinkRecord.master_id == cte.c.master_id,
                LinkRecord.person_id == cte.c.person_id,
            )
        )
    )

    # Union the base and recursive parts
    cte = cte.union_all(recursive)

    # Execute the recursive query
    results = jtrace.execute(select(cte)).all()

    for master_id, person_id in results:
        mr_set.add(master_id)
        pr_set.add(person_id)

    return mr_set, pr_set


def _find_related_links(jtrace: Session, link_records: Query):
    return jtrace.query(LinkRecord.master_id, LinkRecord.person_id).filter(
        (LinkRecord.master_id.in_({r.master_id for r in link_records}))
        | (LinkRecord.person_id.in_({r.person_id for r in link_records}))
    )


def native_recursive(
    jtrace: Session, seen_master_ids: set[int], seen_person_ids: set[int]
):
    links = jtrace.query(LinkRecord.master_id, LinkRecord.person_id).filter(
        LinkRecord.master_id.in_(seen_master_ids)
        | LinkRecord.person_id.in_(seen_person_ids)
    )
    previous_count = 0
    current_count = links.count()

    while current_count != previous_count:
        previous_count = current_count
        links = _find_related_links(jtrace, links)
        current_count = links.count()

    mr_set = set()
    pr_set = set()
    for item in links.all():
        mr_set.add(item.master_id)
        pr_set.add(item.person_id)

    return mr_set, pr_set


if __name__ == "__main__":
    results:dict[Any, Any] = {}

    def _check_results(actual:tuple, masterrecord:MasterRecord):
        if actual[0] != results[ masterrecord.id]:
            print(f"WARNING: Different results for { masterrecord.id}")
            print("Expected:")
            print(results[ masterrecord.id])
            print("Got:")
            print(actual[0])

    print("Setting up...")
    session = JtraceSession()
    records:List[MasterRecord] = session.query(MasterRecord).limit(100).all()
    print("Starting test...")

    for record in records:
        results[record.id] = {}

    with Timer("Native"):
        for record in records:
            r = native(session, {record.id}, set())
            results[record.id] = r[0]

    with Timer("Native Recursive"):
        for record in records:
            r = native_recursive(session, {record.id}, set())
            _check_results(r,record)

    with Timer("SQL"):
        for record in records:
            r = sql(session, {record.id}, set())
            _check_results(r,record)
