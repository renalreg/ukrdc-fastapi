"""Modules which relate to the Repository System Tables"""
from sqlalchemy import Column, Integer, String

from .ukrdc import Base


class PKBLink(Base):
    __tablename__ = "pkb_links"

    id = Column(Integer, primary_key=True)
    link = Column(String)
    link_name = Column(String)
    coding_standard = Column(String)
    code = Column(String)
