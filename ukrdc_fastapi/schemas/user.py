from typing import Optional

from pydantic import Extra

from .base import OrmModel


class UserPreferences(OrmModel, extra=Extra.ignore):
    search_show_ukrdc: bool = False


class UserPreferencesRequest(OrmModel):
    search_show_ukrdc: Optional[bool]
