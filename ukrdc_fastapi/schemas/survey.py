import datetime
from typing import List

from .base import ORMModel


class SurveyQuestionSchema(ORMModel):
    id: str
    questiontypecode: str
    response: str


class SurveyScoreSchema(ORMModel):
    id: str
    value: str
    scoretypecode: str


class SurveyLevelSchema(ORMModel):
    id: str
    value: str
    leveltypecode: str


class SurveySchema(ORMModel):
    questions: List[SurveyQuestionSchema]
    scores: List[SurveyScoreSchema]
    levels: List[SurveyLevelSchema]

    id: str
    pid: str
    surveytime: datetime.datetime
    surveytypecode: str
    enteredbycode: str
    enteredatcode: str
