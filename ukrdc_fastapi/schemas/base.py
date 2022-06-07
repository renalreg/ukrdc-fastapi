from fastapi_hypermodel import HyperModel
from pydantic import validator
from sqlalchemy.orm import Query


def _to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class JSONModel(HyperModel):
    class Config:
        orm_mode = True
        alias_generator = _to_camel
        allow_population_by_field_name = True


class OrmModel(JSONModel):
    @validator("*", pre=True)
    def evaluate_lazy_columns(cls, value):  # pylint: disable=no-self-argument
        """
        Find field values with Query type and evaluate to actual data.

        When lazy-loading relationships in SQLAlchemy, the ORM will return
        a query object instead of joining the data.

        E.g. An instance of Patient, we will call `patient`.
        Calling `patient.addresses` will not actually return a list of
        Address objects, but rather a Query object which can be further
        filtered. This breaks serialization since the schema is expecting
        an actual list of Address objects. This custom validator finds
        such fields, and expands the data by calling the .all() method.
        """
        if isinstance(value, Query):
            return value.all()
        return value
