from fastapi.openapi.utils import get_openapi
from ukrdc_fastapi.main import app
import json
from pathlib import Path

parent = Path(__file__).resolve().parent

with open(parent.joinpath("openapi.json"), "w", encoding="utf-8") as f:
    json.dump(
        get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        ),
        f,
    )
