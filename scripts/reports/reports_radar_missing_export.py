"""Simple script to export RADAR-missing patients for a facility to an Excel-friendly CSV file.

Run with the app running locally. Adjust BASE_URL and FACILITY_CODE as needed.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


BASE_URL: str = "http://localhost:8000"
FACILITY_CODE: str = "RCSLB"
PAGE_SIZE: int = 100
OUTPUT_FILENAME: str = "radar_missing_RCSLB.csv"
AUTH_TOKEN: Optional[str] = None  # Set to a bearer token string if your API requires auth


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
        page = 1
        while True:
            current = fetch_page(client, page)

            if not current.items:
                break

            results.extend(current.items)

            if current.page * current.size >= current.total:
                break

            page += 1

    return results


def write_csv(rows: List[Dict[str, Any]], filename: str) -> None:
    if not rows:
        print("No rows returned from API; nothing to write.")
        return

    # Use all keys from the first row as columns; Excel will happily open the CSV
    fieldnames = sorted(rows[0].keys())

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {len(rows)} rows to {filename}")


def main() -> None:
    print(f"Fetching RADAR-missing patients for facility {FACILITY_CODE} from {BASE_URL}...")
    rows = fetch_all_results()
    write_csv(rows, OUTPUT_FILENAME)


if __name__ == "__main__":
    main()
