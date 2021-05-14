import json
import os

from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies.database import JtraceSession
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
from ukrdc_fastapi.utils.filters.empi import find_related_masterrecords


def find_ukrdc_dupes(jtrace: Session):
    rfile = "dupes.json"

    if os.path.isfile(rfile):
        with open(rfile, "r") as f:
            results = json.load(f)
        print("Loaded results:")
        print(results)
    else:
        results = {"cleared": [], "failed": {}}

    print("Fetching records")
    records: MasterRecord = jtrace.query(MasterRecord).filter(
        MasterRecord.id.notin_(results["cleared"])
    )

    for record in records:
        print(f"Processing record {record.id}")
        related_ukrdc_records = find_related_masterrecords(record, jtrace).filter(
            MasterRecord.nationalid_type == "UKRDC"
        )
        if related_ukrdc_records.count() > 1:
            print(f"Multiple UKRDC IDs found for {record.id}")

            matched_ids = [r.id for r in related_ukrdc_records]
            results["failed"][record.id] = matched_ids

        else:
            results["cleared"].append(record.id)

        with open(rfile, "w") as f:
            f.write(json.dumps(results))


if __name__ == "__main__":
    session = JtraceSession()

    find_ukrdc_dupes(session)
