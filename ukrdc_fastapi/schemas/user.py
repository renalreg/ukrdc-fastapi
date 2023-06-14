from typing import Optional

from pydantic import Extra, Field

from .base import OrmModel


class UserPreferences(OrmModel, extra=Extra.ignore):
    """User preferences"""

    placeholder: bool = Field(
        default=False, description="Placeholder preference, does not do anything"
    )


class UserPreferencesRequest(OrmModel):
    """A request to update user preferences"""

    placeholder: Optional[bool] = Field(
        default=None, description="Placeholder preference, does not do anything"
    )
