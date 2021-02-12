import datetime
from typing import List

from .base import OrmModel


class SurveyQuestionSchema(OrmModel):
    id: str
    questiontypecode: str
    response: str


class SurveyScoreSchema(OrmModel):
    id: str
    value: str
    scoretypecode: str


class SurveyLevelSchema(OrmModel):
    id: str
    value: str
    leveltypecode: str


class SurveySchema(OrmModel):
    questions: List[SurveyQuestionSchema]
    scores: List[SurveyScoreSchema]
    levels: List[SurveyLevelSchema]

    id: str
    pid: str
    surveytime: datetime.datetime
    surveytypecode: str
    enteredbycode: str
    enteredatcode: str
