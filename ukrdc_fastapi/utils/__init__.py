from typing import Optional

import requests
from fastapi import HTTPException
from requests.exceptions import RequestException

from ukrdc_fastapi.config import settings


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


def post_mirth_message(mirth_path: str, message: str):
    """Post message to the Mirth HTTP listener."""
    mirth_path_clean = mirth_path.strip("/")
    mirth_url = settings.mirth_url

    url = f"{mirth_url}/{mirth_path_clean}/"
    headers = {"content-type": "application/xml"}

    return requests.post(url, data=message, headers=headers)


def post_mirth_message_and_catch(
    mirth_path: str, message: str, post: Optional[bool] = True
):
    """Post message to the Mirth HTTP listener, returning a response for our API."""
    if post is None:
        post = True
    if post:
        try:
            post_mirth_message(mirth_path, message.strip())
            status = "success"
        except RequestException as e:
            raise HTTPException(502, detail="Error exporting data to Mirth") from e
    else:
        status = "ignored"
    return {"status": status, "message": message}
