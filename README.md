# UKRDC-FastAPI

[![codecov](https://codecov.io/gh/renalreg/ukrdc-fastapi/branch/main/graph/badge.svg?token=5GYR8M6G1W)](https://codecov.io/gh/renalreg/ukrdc-fastapi)

## Project Status

This rewrite of the UKRDC API is currently in development, and is not yet being used in production.

## Developer Installation

- Install Poetry
- Run `poetry install`

## Basic Installation

- `pip install .`

## Run the server

- `poetry run uvicorn ukrdc_fastapi.main:app`

## Developer notes

### Local CORS

On some oeprating systems and environments, it may be difficult to properly set a CORS policy for local development. In these cases, add `ALLOWED_ORIGINS=["*"]` to your `.env` file.

### VSCode config for auto-formatting

```json
{
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### Build ARCHITECTURE.md

- Install `pipx`
- `pipx install archmd`
- `archmd . --out "ARCHITECTURE.md" --title="UKRDC-FastAPI Architecture"`
