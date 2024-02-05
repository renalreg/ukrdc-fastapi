import datetime
from contextlib import suppress
from time import time
from typing import Generator, Optional, Union


class Timer:
    def __init__(self, description):
        self.description = description
        self.start = time()
        self.end = None

    def __enter__(self):
        self.start = time()

    def __exit__(self, *_):
        self.end = time()
        print(f"{self.description}: {self.end - self.start}")


def build_db_uri(
    driver: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    name: Optional[str] = None,
) -> str:
    """Construct a database URI from required parameters

    Args:
        driver (str): Database driver (sqlite, postgresql, etc.)
        host (Optional[str]): [description]. Database hostname/IP
        port (Optional[int]): [description]. Database port
        user (Optional[str]): [description]. Database username
        password (Optional[str]): [description]. Database password
        name (Optional[str]): [description]. Database name

    Returns:
        [str]: Full database URI
    """
    if driver == "sqlite":
        return f"{driver}:///{name}"
    return f"{driver}://{user}:{password}@{host}:{port}/{name}"


def parse_date(date_string: Optional[str]) -> Optional[datetime.datetime]:
    """Convert a fuzzy date string into a datetime object

    Args:
        date_string (Optional[str]): Formatted date string

    Returns:
        Optional[datetime.datetime]: Datetime object if parsing was successful
    """
    if not date_string:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        with suppress(ValueError):
            return datetime.datetime.strptime(date_string, fmt)
    return None


def daterange(
    start_date: Union[datetime.date, datetime.datetime],
    end_date: Union[datetime.date, datetime.datetime],
) -> Generator[datetime.date, None, None]:
    """
    Generate a range of dates between two dates, separated by one day

    Args:
        start_date (datetime.date): Start date
        end_date (datetime.date): End date

    Yields:
        datetime.date: Date between start and end
    """
    # "Round" datetimes to dates
    if isinstance(start_date, datetime.datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime.datetime):
        end_date = end_date.date()

    # Add one day to end date to include it in the range
    for day_offset in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(day_offset)
