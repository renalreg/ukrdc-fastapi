from pydantic import BaseModel, validator
from sqlalchemy.orm import Query


class ORMModel(BaseModel):
    class Config:
        orm_mode = True

    @validator("*", pre=True)
    def evaluate_lazy_columns(cls, v):
        if isinstance(v, Query):
            return v.all()
        return v


class LazyORMModel(ORMModel):
    @validator("*", pre=True)
    def evaluate_lazy_columns(cls, v):
        if isinstance(v, Query):
            return v.all()
        return v
