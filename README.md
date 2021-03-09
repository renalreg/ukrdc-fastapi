# UKRDC-FastAPI

[![codecov](https://codecov.io/gh/renalreg/ukrdc-fastapi/branch/main/graph/badge.svg?token=5GYR8M6G1W)](https://codecov.io/gh/renalreg/ukrdc-fastapi)

## Developer Installation

- Install Poetry
- Run `poetry install`

## Basic Installation

- `pip install .`

## Run the server

- `poetry run uvicorn ukrdc_fastapi.main:app`

## Developer notes

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
