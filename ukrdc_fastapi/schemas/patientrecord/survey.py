import datetime
from typing import Optional

from pydantic import Field, model_validator

from ukrdc_fastapi.utils.codes import yhq

from ..base import OrmModel


class SurveyQuestionSchema(OrmModel):
    """Information about a single survey question"""

    id: str = Field(..., description="Question ID")
    questiontypecode: str = Field(..., description="Question type code")
    response: str = Field(..., description="Question response")

    question_group: Optional[str] = Field(None, description="Question group")
    question_type: Optional[str] = Field(None, description="Question type")
    response_text: Optional[str] = Field(None, description="Question response text")

    @model_validator(mode="after")
    def convert_codes(self):
        """
        Lookup question type and response codes in order to provide
        human-readable data from the database codes. Also allocates
        a question group where one is provided.
        """
        # Look for a matching code
        metadata = yhq.METADATA.get(self.questiontypecode)
        if not metadata:
            return self

        self.question_type = metadata["question"]
        self.question_group = metadata["group"]
        self.response_text = metadata["answers"].get(self.response)

        return self


class SurveyScoreSchema(OrmModel):
    """Information about a single survey score"""

    id: str = Field(..., description="Survey score ID")
    value: str = Field(..., description="Survey score value")
    scoretypecode: str = Field(..., description="Survey score type code")


class SurveyLevelSchema(OrmModel):
    """Information about a single survey level"""

    id: str = Field(..., description="Survey level ID")
    value: str = Field(..., description="Survey level value")
    leveltypecode: str = Field(..., description="Survey level type code")


class SurveySchema(OrmModel):
    """Information about a single survey"""

    questions: list[SurveyQuestionSchema] = Field(..., description="Survey questions")
    scores: list[SurveyScoreSchema] = Field(..., description="Survey scores")
    levels: list[SurveyLevelSchema] = Field(..., description="Survey levels")

    id: str = Field(..., description="Survey ID")
    pid: str = Field(..., description="Patient ID")
    surveytime: datetime.datetime = Field(..., description="Survey timestamp")
    surveytypecode: str = Field(..., description="Survey type code")
    enteredbycode: Optional[str] = Field(None, description="Survey author code")
    enteredatcode: Optional[str] = Field(None, description="Survey organization code")