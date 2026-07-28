from typing import Optional

from pydantic import Field

from .base import OrmModel


class UserPreferences(OrmModel, extra="ignore"):
    """User preferences"""

    placeholder: bool = Field(
        default=False, description="Placeholder preference, does not do anything"
    )


class UserPreferencesRequest(OrmModel):
    """A request to update user preferences"""

    placeholder: bool | None = Field(
        default=None, description="Placeholder preference, does not do anything"
    )
