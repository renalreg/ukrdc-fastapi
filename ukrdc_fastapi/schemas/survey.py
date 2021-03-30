import datetime

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
    questions: list[SurveyQuestionSchema]
    scores: list[SurveyScoreSchema]
    levels: list[SurveyLevelSchema]

    id: str
    pid: str
    surveytime: datetime.datetime
    surveytypecode: str
    enteredbycode: str
    enteredatcode: str
