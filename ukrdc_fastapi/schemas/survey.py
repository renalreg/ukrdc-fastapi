import datetime
from typing import Optional

from pydantic import root_validator

from ukrdc_fastapi.utils.codes import yhq

from .base import OrmModel


class SurveyQuestionSchema(OrmModel):
    id: str
    questiontypecode: str
    response: str

    question_group: Optional[str]
    question_type: Optional[str]
    response_text: Optional[str]

    @root_validator
    def convert_codes(cls, values):  # pylint: disable=no-self-argument
        """
        Lookup question type and response codes in order to provide
        human-readable data from the database codes. Also allocates
        a question group where one is provided.
        """
        # Look for a matching code
        metadata = yhq.METADATA.get(values["questiontypecode"])
        if not metadata:
            return values

        values["question_type"] = metadata["question"]
        values["question_group"] = metadata["group"]
        values["response_text"] = metadata["answers"].get(values["response"])

        return values


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
    enteredbycode: Optional[str]
    enteredatcode: Optional[str]
