import datetime
from time import time
from typing import Optional


class Timer(object):
    def __init__(self, description):
        self.description = description

    def __enter__(self):
        self.start = time()

    def __exit__(self, type, value, traceback):
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
        try:
            return datetime.datetime.strptime(date_string, fmt)
        except ValueError:
            pass
    return None
