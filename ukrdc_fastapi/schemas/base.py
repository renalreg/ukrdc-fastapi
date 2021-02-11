from pydantic import BaseModel


class ORMModel(BaseModel):
    class Config:
        orm_mode = True
