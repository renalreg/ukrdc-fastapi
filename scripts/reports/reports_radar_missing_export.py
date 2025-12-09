"""Simple script to export RADAR-missing patients for a facility to an Excel-friendly CSV file.

Run with the app running locally. Adjust BASE_URL and FACILITY_CODE as needed.
If required this could easily be generalized for all the reports.
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


BASE_URL: str = "http://localhost:8000"
FACILITY_CODE: str = "RCSLB"
PAGE_SIZE: int = 100_000
OUTPUT_FILENAME: str = "radar_missing_RCSLB.xlsx"
AUTH_TOKEN: Optional[str] = (
    None  # Set to a bearer token string if your API requires auth
)


@dataclass
class Page:
    items: List[Dict[str, Any]]
    total: int
    page: int
    size: int


def build_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {"Accept": "application/json"}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return headers


def fetch_page(client: httpx.Client, page: int) -> Page:
    url = f"{BASE_URL}/api/facilities/{FACILITY_CODE}/reports/radar_missing"

    response = client.get(url, params={"page": page, "size": PAGE_SIZE})
    response.raise_for_status()

    data = response.json()

    items = data.get("items", [])
    total = int(data.get("total", len(items)))
    size = int(data.get("size", PAGE_SIZE))
    current_page = int(data.get("page", page))

    return Page(items=items, total=total, page=current_page, size=size)


def fetch_all_results() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    with httpx.Client(headers=build_headers(), timeout=30.0) as client:
        # Fetch everything in a single request by using a very large page size.
        current = fetch_page(client, page=1)

        if current.items:
            results.extend(current.items)

    return results


def results_to_dataframe(results: List[Dict[str, Any]]) -> pd.DataFrame:
    rows_for_df: List[Dict[str, Any]] = []

    for item in results:
        pid = item.get("pid")
        sending_facility = item.get("sendingfacility")
        sending_extract = item.get("sendingextract")
        local_patient_id = item.get("localpatientid")
        ukrdcid = item.get("ukrdcid")

        program_memberships = item.get("programMemberships", [])
        if program_memberships:
            for membership in program_memberships:
                row: Dict[str, Any] = {
                    "pid": pid,
                    "sendingfacility": sending_facility,
                    "sendingextract": sending_extract,
                    "localpatientid": local_patient_id,
                    "ukrdcid": ukrdcid,
                    **membership,
                }
                rows_for_df.append(row)
        else:
            rows_for_df.append(
                {
                    "pid": pid,
                    "sendingfacility": sending_facility,
                    "sendingextract": sending_extract,
                    "localpatientid": local_patient_id,
                    "ukrdcid": ukrdcid,
                }
            )

    return pd.DataFrame(rows_for_df)


def main() -> None:
    print(
        f"Fetching RADAR-missing patients for facility {FACILITY_CODE} from {BASE_URL}..."
    )
    rows = fetch_all_results()
    df = results_to_dataframe(rows)
    df.to_excel(OUTPUT_FILENAME, index=False)


if __name__ == "__main__":
    main()
