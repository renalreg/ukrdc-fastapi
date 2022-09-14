from typing import Optional

from pydantic import Extra, Field

from .base import OrmModel


class UserPreferences(OrmModel, extra=Extra.ignore):
    search_show_ukrdc: bool = Field(
        default=False, description="Show UKRDC records in search results by default"
    )


class UserPreferencesRequest(OrmModel):
    search_show_ukrdc: Optional[bool] = Field(
        default=None, description="Show UKRDC records in search results by default"
    )
