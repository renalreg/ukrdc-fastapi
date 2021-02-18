from typing import Any, Dict, Iterable, Optional

import requests
from fastapi import Request

from .config import settings

__all__ = ["build_db_uri", "post_mirth_message", "inject_href", "inject_hrefs"]


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


def post_mirth_message(mirth_path, message):
    """Post message to the Mirth HTTP listener."""
    mirth_path_clean = mirth_path.strip("/")
    mirth_url = settings.mirth_url

    url = f"{mirth_url}/{mirth_path_clean}/"
    headers = {"content-type": "application/xml"}

    return requests.post(url, data=message, headers=headers)


def inject_href(
    request: Request,
    item: Any,
    view: str,
    var_dict: Dict[str, str],
) -> None:
    """Inject an href attribute into some object

    Args:
        request (Request): FastAPI request object
        item (Any): Object in which to inject href
        view (str): Name of the target view function
        var_dict (Dict[str, str]): Dictionary mapping view function
            arguments to object attributes. E.g. {"item_id": "id"}
            will set the view function argument `item_id` to the value of item.id
    """
    kwargs: Dict[str, Any] = {k: getattr(item, v) for k, v in var_dict.items()}
    item.href = request.url_for(view, **kwargs)


def inject_hrefs(
    request: Request,
    items: Iterable[Any],
    view: str,
    var_dict: Dict[str, str],
) -> None:
    """Inject href attributes into some iterable collection of objects

    Args:
        request (Request): FastAPI request object
        items (Iterable[Any]): Object in which to inject href
        view (str): Name of the target view function
        var_dict (Dict[str, str]): Dictionary mapping view function
            arguments to object attributes. E.g. {"item_id": "id"}
            will set the view function argument `item_id` to the value of item.id
    """
    for item in items:
        inject_href(request, item, view, var_dict)
