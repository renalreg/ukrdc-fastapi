# routers

FastAPI routers creating the actual API structure.

These routes provide data marshalling, basic access controls, and some extra data processing functionality. However, virtually all query logic should be in the `query` submodule.

Currently, only the `/api` top level router is being used, however in future we may introduce separate top-level routers for functionality like a FHIR-compatible API.

If you're browsing the code to get an overview of structure, you can traverse the API tree starting from `routers/api/__init__.py`. The router in that file is mounted by the FastAPI app object.
