"""Simple script to export RADAR-missing patients for a facility to an Excel-friendly CSV file.

Run with the app running locally. Adjust BASE_URL and FACILITY_CODES as needed.
If required this could easily be generalized for all the reports.
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path
import httpx


BASE_URL: str = "http://localhost:8000"
FACILITY_CODES: List[str] =  [
    "RAJ",
    "RAQ01",
    "RCSLB",
    "RH8",
    "RHW01",
#    "RJZ", Kings
    "RK7CC",
    "RL403", 
    "RNJ00",
]

PAGE_SIZE: int = 100_000
OUTPUT_PATH: Path = (
    Path("scripts") / "analytics" / "output/" / "radar_missing_{facility_code}.xlsx"
)
AUTH_TOKEN: Optional[str] = (
    None  # Set to a bearer token string if your API requires auth
)

FACILITY_CODE: str = ""

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

    try:
        response = client.get(url, params={"page": page, "size": PAGE_SIZE}, timeout=60.0)
        response.raise_for_status()
    except httpx.RequestError as e:
        print(f"Error fetching data for {FACILITY_CODE}: {str(e)}")
        return Page(items=[], total=0, page=page, size=PAGE_SIZE)

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
    for facility_code in FACILITY_CODES:
        global FACILITY_CODE
        FACILITY_CODE = facility_code
        print(
            f"Fetching RADAR-missing patients for facility {FACILITY_CODE} from {BASE_URL}..."
        )
        try:
            rows = fetch_all_results()
            if rows:
                df = results_to_dataframe(rows)
                df.to_excel(str(OUTPUT_PATH).format(facility_code=facility_code), index=False)
        except Exception as e:
            print(f"Failed to process {facility_code}: {str(e)}")
            continue


if __name__ == "__main__":
    main()
