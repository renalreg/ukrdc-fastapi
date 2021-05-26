# UKRDC-FastAPI Architecture

  - [ukrdc_fastapi](#ukrdc_fastapi)
    - [ukrdc_fastapi/routers](#ukrdc_fastapi-routers)
    - [ukrdc_fastapi/dependencies](#ukrdc_fastapi-dependencies)
    - [ukrdc_fastapi/utils](#ukrdc_fastapi-utils)
    - [ukrdc_fastapi/schemas](#ukrdc_fastapi-schemas)
    - [ukrdc_fastapi/query](#ukrdc_fastapi-query)

<a name="ukrdc_fastapi"></a>

## UKRDC FastAPI Application

<a name="ukrdc_fastapi-routers"></a>

### routers

FastAPI routers creating the actual API structure.

These routes provide data marshalling, basic access controls, and some extra data processing functionality. However, virtually all query logic should be in the `query` submodule.

Currently, only the `/api` top level router is being used, however in future we may introduce separate top-level routers for functionality like a FHIR-compatible API.

If you're browsing the code to get an overview of structure, you can traverse the API tree starting from `routers/api/__init__.py`. The router in that file is mounted by the FastAPI app object.

<a name="ukrdc_fastapi-dependencies"></a>

### dependencies

Read <https://fastapi.tiangolo.com/tutorial/dependencies/>

This contains all dependencies used throughout the FastAPI application.

#### dependencies/okta

The `okta` submodule could (and probably should?) stand as its own library. It extends the FastAPI auth model to include Okta-specific code, integrating with the interactive documentation, and enabling extras such as user groups/permissions.

<a name="ukrdc_fastapi-utils"></a>

### utils

Miscellaneous common utilities.

#### utils/codes

Utilities related to parsing, resolving, or converting codes.

#### utils/search

Utilities related to fuzzy-searching the dataset.

<a name="ukrdc_fastapi-schemas"></a>

### schemas

Pydantic data models/schemas for marshalling database data.

Each submodule here provides schemas for a different category of object within the UKRDC data model, however they essentially all inherit from `base.py:OrmModel`.

This model provides two key bits of functionality. Firstly, it will alias fieldnames to be JSON-friendly. That is, it converts Python `snake_case` field names into JSON-style `camelCase` field names.

Secondly, it uses a validator to lazy-evaluate columns. When lazy-loading relationships in SQLAlchemy, the ORM will returnm a query object instead of joining the data.

E.g. An instance of Patient, we will call `patient`. Calling `patient.addresses` will not actually return a list of `Address` objects, but rather a `Query` object which can be further filtered. This breaks serialization since the schema is expecting an actual list of `Address` objects. This custom validator finds such fields, and expands the data by calling the `.all()` method.

<a name="ukrdc_fastapi-query"></a>

### query

This really is the key part of this application. The modules here handle retreiving, filtering, and sorting database queries before being passed to the API router for marshalling.

Critically, each module here also includes methods for handling permission-based access.

The API router is able to either grant or deny access to an API route based on permissions, however it cannot restrict access to resources based on properties of those resources. For example, a patient record should only be accessible by users with permission to view records from their unit/facility.

Additionally, routes mapping to lists of resources, for example a list of patient records, need to be filtered based on permission. We cannot simply allow or deny access.

Each module here should include an `_apply_query_permissions` function, which takes a query for a list of resources and filters based on user permissions. Also, an `_assert_permission` function handles a users access to a specific resource, raising a suitable HTTP exception if the user does not have permission to access this resource.

Note, that the permission-based filtering here augments API-level access control. For example, a user may have access to a patientrecord because of unit/facility permissions, but the user cannot modify that resource if they don't have write permission. That denial of access is handled by the API route security.
