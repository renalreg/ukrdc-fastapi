from typing import Optional

from sqlalchemy import JSON, Column, String
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Mapped, mapped_column  # type: ignore


class Base(DeclarativeBase):
    pass


class UserPreference(Base):
    __tablename__ = "user_preference"

    uid: Mapped[str] = mapped_column(
        String, primary_key=True, nullable=False
    )  # User ID
    key: Mapped[str] = mapped_column(
        String, primary_key=True, nullable=False
    )  # Preference key
    val: Mapped[Optional[str]] = mapped_column(
        JSON
    )  # Preference value, as a JSON primitive, array, or object
