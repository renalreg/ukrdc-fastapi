# UKRDC-FastAPI

[![codecov](https://codecov.io/gh/renalreg/ukrdc-fastapi/branch/main/graph/badge.svg?token=5GYR8M6G1W)](https://codecov.io/gh/renalreg/ukrdc-fastapi)

## Developer Installation

### Prerequisites

- Create a `.env` file with Mirth and database credentials, for example (replacing "\*\*\*\*" with the actual credentials):

```
UKRDC_HOST="db.ukrdc.nhs.uk"
JTRACE_HOST="db.ukrdc.nhs.uk"
ERRORS_HOST="db.ukrdc.nhs.uk"

UKRDC_PASS="****"
JTRACE_PASS="****"
ERRORS_PASS="****"

MIRTH_URL="https://mirth.ukrdc.nhs.uk/api"
MIRTH_VERIFY_SSL=false
MIRTH_USER="webapi"
MIRTH_PASS="****"

APP_CLIENT_ID=0oan98slw3m4mnhxq5d6
SWAGGER_CLIENT_ID="0oan75eooLX2DcdQK5d6"
```

- Ensure a local Redis instance is running locally on port 6379

### Installation

- Install Poetry
- Run `poetry install`

## Run the server

- `poetry run uvicorn ukrdc_fastapi.main:app`

## Developer notes

### Pre-commit hooks

Included in the repo is a pre-commit config to run Black and isort before committing.

To install/enable the hooks, run

```
poetry run pre-commit install
```

### Local CORS

On some oeprating systems and environments, it may be difficult to properly set a CORS policy for local development. In these cases, add `allow_origins=["*"]` to your `.env` file.

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
