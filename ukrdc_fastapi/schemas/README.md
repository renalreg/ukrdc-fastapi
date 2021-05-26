# schemas

Pydantic data models/schemas for marshalling database data.

Each submodule here provides schemas for a different category of object within the UKRDC data model, however they essentially all inherit from `base.py:OrmModel`.

This model provides two key bits of functionality. Firstly, it will alias fieldnames to be JSON-friendly. That is, it converts Python `snake_case` field names into JSON-style `camelCase` field names.

Secondly, it uses a validator to lazy-evaluate columns. When lazy-loading relationships in SQLAlchemy, the ORM will returnm a query object instead of joining the data.

E.g. An instance of Patient, we will call `patient`. Calling `patient.addresses` will not actually return a list of `Address` objects, but rather a `Query` object which can be further filtered. This breaks serialization since the schema is expecting an actual list of `Address` objects. This custom validator finds such fields, and expands the data by calling the `.all()` method.
