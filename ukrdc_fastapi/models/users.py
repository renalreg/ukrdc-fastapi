from sqlalchemy import JSON, Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserPreference(Base):
    __tablename__ = "user_preference"

    uid = Column(String, primary_key=True, nullable=False)  # User ID
    key = Column(String, primary_key=True, nullable=False)  # Preference key
    val = Column(JSON)  # Preference value, as a JSON primitive, array, or object
