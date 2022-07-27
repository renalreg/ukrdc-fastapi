from typing import Optional

from pydantic import Extra

from .base import OrmModel


class ReadUserPreferences(OrmModel, extra=Extra.ignore):
    search_show_ukrdc: bool = False


class UpdateUserPreferences(OrmModel):
    search_show_ukrdc: Optional[bool]
